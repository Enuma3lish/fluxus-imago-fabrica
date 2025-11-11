"""
FastAPI Payment Service - Main Application
"""
from fastapi import FastAPI, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
import httpx
import logging
from config import get_settings
from ecpay.client import ECPayClient

# Setup logging
import os
os.makedirs('logs', exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/payment_service.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Payment Service API",
    description="FastAPI Payment Microservice with ECPay Integration",
    version="1.0.0"
)

# Get settings
settings = get_settings()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, settings.backend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize ECPay client
ecpay_client = ECPayClient(
    merchant_id=settings.ecpay_merchant_id,
    hash_key=settings.ecpay_hash_key,
    hash_iv=settings.ecpay_hash_iv,
    payment_url=settings.ecpay_payment_url
)


# Pydantic models
class PaymentCreateRequest(BaseModel):
    """Request model for creating payment"""
    order_id: str = Field(..., description="Order ID from backend")
    order_number: str = Field(..., description="Order number for payment tracking")
    amount: int = Field(..., gt=0, description="Payment amount (integer)")
    item_name: str = Field(..., description="Item name")
    description: str = Field(default="Payment", description="Payment description")
    payment_method: str = Field(default="Credit", description="Payment method (Credit/ATM/CVS/BARCODE)")


class PaymentResponse(BaseModel):
    """Response model for payment"""
    success: bool
    payment_url: Optional[str] = None
    form_data: Optional[Dict[str, Any]] = None
    message: Optional[str] = None


# Helper functions
async def get_order_from_backend(order_id: str) -> Dict[str, Any]:
    """Fetch order details from Django backend"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{settings.backend_url}/api/orders/{order_id}/")
            response.raise_for_status()
            return response.json()
    except Exception as e:
        logger.error(f"Failed to fetch order from backend: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch order details")


async def update_order_status(order_id: str, status: str, payment_data: Dict[str, Any]) -> bool:
    """Update order status in Django backend"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.patch(
                f"{settings.backend_url}/api/orders/{order_id}/",
                json={
                    "status": status,
                    "payment_data": payment_data
                }
            )
            response.raise_for_status()
            return True
    except Exception as e:
        logger.error(f"Failed to update order status: {str(e)}")
        return False


# API endpoints
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Payment Service",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.post("/payment/ecpay/create/", response_model=PaymentResponse)
async def create_ecpay_payment(payment_request: PaymentCreateRequest):
    """
    Create ECPay payment

    This endpoint creates a payment request to ECPay and returns
    the payment form data that needs to be submitted to ECPay.
    """
    try:
        # Generate unique merchant trade number for retry payments
        # ECPay doesn't allow duplicate MerchantTradeNo, so we append timestamp
        from datetime import datetime as dt
        timestamp_suffix = dt.now().strftime('%H%M%S')  # HHMMSS format

        # If order_number is already max length (20 chars), use it as base
        # Otherwise append timestamp to make it unique for retries
        if len(payment_request.order_number) >= 14:
            # Truncate to 14 chars and add 6-digit timestamp
            merchant_trade_no = f"{payment_request.order_number[:14]}{timestamp_suffix}"
        else:
            merchant_trade_no = f"{payment_request.order_number}{timestamp_suffix}"

        # Ensure it doesn't exceed 20 chars
        merchant_trade_no = merchant_trade_no[:20]

        merchant_trade_date = datetime.now().strftime('%Y/%m/%d %H:%M:%S')

        logger.info(f"Original order number: {payment_request.order_number}, Merchant trade no: {merchant_trade_no}")

        # Store mapping in Redis for callback processing (expires in 24 hours)
        import redis
        redis_client = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_db,
            password=settings.redis_password if settings.redis_password else None,
            decode_responses=True
        )
        redis_client.setex(
            f"payment:merchant_trade_no:{merchant_trade_no}",
            86400,  # 24 hours
            payment_request.order_number
        )
        logger.info(f"Stored mapping: {merchant_trade_no} -> {payment_request.order_number}")

        # Create payment
        # OrderResultURL must be publicly accessible for ECPay to redirect
        payment_service_public_url = "http://localhost:8001"  # Public URL for ECPay

        payment_data = ecpay_client.create_payment(
            merchant_trade_no=merchant_trade_no,
            merchant_trade_date=merchant_trade_date,
            total_amount=payment_request.amount,
            trade_desc=payment_request.description,
            item_name=payment_request.item_name,
            return_url=settings.ecpay_callback_url,  # Backend callback for order update
            order_result_url=f"{payment_service_public_url}/payment/ecpay/result/",  # POST to GET converter
            client_back_url=settings.frontend_url,  # User return button
            choose_payment=payment_request.payment_method
        )

        # Note: Order status will be updated when payment callback is received
        # We don't update it here to avoid authentication issues
        logger.info(f"Created ECPay payment for order: {merchant_trade_no}")

        return PaymentResponse(
            success=True,
            payment_url=payment_data['action_url'],
            form_data=payment_data['params'],
            message="Payment created successfully"
        )

    except Exception as e:
        logger.error(f"Failed to create payment: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/payment/ecpay/result/")
async def ecpay_payment_result(request: Request):
    """
    ECPay payment result endpoint (OrderResultURL)

    This endpoint receives POST data from ECPay and redirects to frontend with GET parameters.
    ECPay sends payment result via POST, but Streamlit only accepts GET, so we convert it.
    """
    try:
        # Get form data from ECPay
        form_data = await request.form()
        result_data = dict(form_data)

        logger.info(f"Received payment result: {result_data}")

        # Extract key parameters
        rtn_code = result_data.get('RtnCode', '0')
        merchant_trade_no = result_data.get('MerchantTradeNo', '')
        rtn_msg = result_data.get('RtnMsg', '')
        trade_no = result_data.get('TradeNo', '')

        # Build redirect URL with query parameters
        redirect_params = {
            'RtnCode': rtn_code,
            'MerchantTradeNo': merchant_trade_no,
            'RtnMsg': rtn_msg,
            'TradeNo': trade_no,
            'page': 'payment_result'
        }

        # Create query string
        from urllib.parse import urlencode
        query_string = urlencode(redirect_params)
        redirect_url = f"{settings.frontend_url}?{query_string}"

        logger.info(f"Redirecting to: {redirect_url}")

        # Return HTML with auto-redirect using JavaScript (more reliable than meta refresh)
        return HTMLResponse(content=f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Payment Complete</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                }}
                .container {{
                    text-align: center;
                    padding: 40px;
                    background: rgba(255, 255, 255, 0.1);
                    border-radius: 10px;
                    backdrop-filter: blur(10px);
                }}
                .spinner {{
                    border: 4px solid rgba(255, 255, 255, 0.3);
                    border-top: 4px solid white;
                    border-radius: 50%;
                    width: 50px;
                    height: 50px;
                    animation: spin 1s linear infinite;
                    margin: 20px auto;
                }}
                @keyframes spin {{
                    0% {{ transform: rotate(0deg); }}
                    100% {{ transform: rotate(360deg); }}
                }}
                a {{
                    color: white;
                    text-decoration: underline;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h2>✅ Payment Processed</h2>
                <div class="spinner"></div>
                <p>Redirecting to results page...</p>
                <p><small>If you are not redirected automatically, <a href="{redirect_url}">click here</a>.</small></p>
            </div>
            <script>
                // Redirect after 1 second
                setTimeout(function() {{
                    window.location.href = "{redirect_url}";
                }}, 1000);
            </script>
        </body>
        </html>
        """)

    except Exception as e:
        logger.error(f"Failed to process payment result: {str(e)}")
        return f"<html><body><h1>Error</h1><p>{str(e)}</p></body></html>"


@app.post("/payment/ecpay/callback/")
async def ecpay_payment_callback(request: Request):
    """
    ECPay payment callback endpoint

    This endpoint receives payment notifications from ECPay
    and updates the order status accordingly.
    """
    try:
        # Get form data
        form_data = await request.form()
        callback_data = dict(form_data)

        logger.info(f"Received payment callback: {callback_data}")

        # Verify callback
        if not ecpay_client.verify_callback(callback_data.copy()):
            logger.error("Payment callback verification failed")
            return "0|Verification failed"

        # Extract payment information
        merchant_trade_no = callback_data.get('MerchantTradeNo')
        rtn_code = callback_data.get('RtnCode')
        payment_type = callback_data.get('PaymentType')

        # Get original order number from Redis
        import redis
        redis_client = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_db,
            password=settings.redis_password if settings.redis_password else None,
            decode_responses=True
        )
        original_order_number = redis_client.get(f"payment:merchant_trade_no:{merchant_trade_no}")

        if not original_order_number:
            # Fallback: try to use merchant_trade_no directly (for old orders)
            original_order_number = merchant_trade_no
            logger.warning(f"No mapping found for {merchant_trade_no}, using it directly")
        else:
            logger.info(f"Retrieved mapping: {merchant_trade_no} -> {original_order_number}")

        # Check if payment was successful (RtnCode = 1 means success)
        if rtn_code == '1':
            # Update order status via Celery task
            # This will be processed asynchronously
            from celery_app import process_payment_callback
            process_payment_callback.delay(original_order_number, callback_data)

            logger.info(f"Payment successful for order: {merchant_trade_no}")
            return "1|OK"
        else:
            logger.warning(f"Payment failed for order: {merchant_trade_no}")
            return "0|Payment failed"

    except Exception as e:
        logger.error(f"Error processing payment callback: {str(e)}")
        return "0|Error"


@app.get("/payment/ecpay/return/")
async def ecpay_payment_return(request: Request):
    """
    ECPay payment return endpoint

    This endpoint handles the user return from ECPay payment page.
    """
    return RedirectResponse(url=f"{settings.frontend_url}/payment/result")


@app.get("/payment/invoice/{order_id}/")
async def get_invoice(order_id: str):
    """
    Get invoice for an order

    This endpoint retrieves the invoice details for a completed order.
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{settings.backend_url}/api/invoices/?order={order_id}")
            response.raise_for_status()
            invoices = response.json()

            if invoices and len(invoices['results']) > 0:
                return invoices['results'][0]
            else:
                raise HTTPException(status_code=404, detail="Invoice not found")

    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail="Invoice not found")
    except Exception as e:
        logger.error(f"Failed to get invoice: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/payment/test/")
async def test_payment(order_id: str):
    """
    Test payment endpoint (for development only)

    This endpoint simulates a successful payment for testing purposes.
    """
    if not settings.debug:
        raise HTTPException(status_code=403, detail="Test endpoint not available in production")

    try:
        # Update order to completed
        await update_order_status(
            order_id,
            "completed",
            {
                "test": True,
                "paid_at": datetime.now().isoformat()
            }
        )

        logger.info(f"Test payment completed for order: {order_id}")

        return {
            "success": True,
            "message": "Test payment completed successfully"
        }

    except Exception as e:
        logger.error(f"Test payment failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=settings.debug
    )
