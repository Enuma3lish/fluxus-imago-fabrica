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
        # Get order details from backend
        order = await get_order_from_backend(payment_request.order_id)

        # Prepare payment data
        merchant_trade_no = order['order_number']
        merchant_trade_date = datetime.now().strftime('%Y/%m/%d %H:%M:%S')

        # Create payment
        payment_data = ecpay_client.create_payment(
            merchant_trade_no=merchant_trade_no,
            merchant_trade_date=merchant_trade_date,
            total_amount=payment_request.amount,
            trade_desc=payment_request.description,
            item_name=payment_request.item_name,
            return_url=settings.ecpay_callback_url,
            order_result_url=f"{settings.frontend_url}/payment/result",
            client_back_url=f"{settings.frontend_url}/payment/return",
            choose_payment=payment_request.payment_method
        )

        # Update order status to processing
        await update_order_status(payment_request.order_id, "processing", payment_data)

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

        # Check if payment was successful (RtnCode = 1 means success)
        if rtn_code == '1':
            # Update order status via Celery task
            # This will be processed asynchronously
            from celery_app import process_payment_callback
            process_payment_callback.delay(merchant_trade_no, callback_data)

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
