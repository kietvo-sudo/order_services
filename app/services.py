"""External services integration"""
import json
import logging
import re
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

SHIPMENT_API_BASE_URL = "https://swift-cynde-be-demo-4c30490b.koyeb.app/"


def _parse_address(address_str: str):
    """
    Parse full address into city, district, ward.
    Attempts to extract city information from address string.
    Falls back to default values if parsing fails.
    
    Returns:
        tuple: (city, district, ward)
    """
    if not address_str:
        return ("Ho Chi Minh City", "", "")
    
    address_lower = address_str.lower()
    
    # Common Vietnamese city names
    cities = ["ho chi minh", "hồ chí minh", "hcm", "hanoi", "hà nội", "da nang", "đà nẵng", 
              "can tho", "cần thơ", "hai phong", "hải phòng"]
    
    # Try to find city in address
    found_city = None
    for city in cities:
        if city in address_lower:
            if "ho chi minh" in address_lower or "hồ chí minh" in address_lower or "hcm" in address_lower:
                found_city = "Ho Chi Minh City"
            elif "hanoi" in address_lower or "hà nội" in address_lower:
                found_city = "Hanoi"
            elif "da nang" in address_lower or "đà nẵng" in address_lower:
                found_city = "Da Nang"
            elif "can tho" in address_lower or "cần thơ" in address_lower:
                found_city = "Can Tho"
            elif "hai phong" in address_lower or "hải phòng" in address_lower:
                found_city = "Hai Phong"
            break
    
    # Default to Ho Chi Minh City if not found
    city = found_city or "Ho Chi Minh City"
    
    # Try to extract district (common patterns)
    district = ""
    ward = ""
    
    # Simple extraction - look for common district indicators
    # This is a basic implementation; production should use proper geocoding
    if "district" in address_lower or "quận" in address_lower:
        # Try to extract district number or name
        district_match = re.search(r'(?:district|quận)\s*(\d+)', address_lower)
        if district_match:
            district = f"District {district_match.group(1)}"
    
    return (city, district, ward)


def send_order_to_shipment(order) -> Optional[dict]:
    """
    Send complete order data to shipment API in the expected format
    
    Args:
        order: Order model instance (with items and products loaded)
              Can be an unsaved instance (not yet committed to DB)
        
    Returns:
        Response data from shipment API or None if failed
    """
    url = f"{SHIPMENT_API_BASE_URL}api/shipments"
    
    try:
        logger.info(f"[SHIPMENT API] Starting to prepare order {order.order_code} for shipment API")
        
        # Parse receiver address (city, district, ward)
        # Use customer information as default if receiver information is not available
        receiver_name = order.receiver_name if order.receiver_name else order.customer_name
        receiver_phone = order.receiver_phone if order.receiver_phone else order.customer_phone
        # Use default address if receiver address is empty or None
        # Shipment API requires non-blank address
        receiver_address_str = order.receiver_address if order.receiver_address else "Ho Chi Minh City, Vietnam"
        receiver_city, receiver_district, receiver_ward = _parse_address(receiver_address_str)
        
        # Use receiver address as sender address if sender address is not available
        # This is a common pattern when customer is both sender and receiver
        # Shipment API requires non-blank address
        sender_address = receiver_address_str if receiver_address_str else "Ho Chi Minh City, Vietnam"
        
        # Calculate package dimensions and weight from items
        # For now, use default values or calculate from items
        total_weight = sum(item.quantity * 0.5 for item in order.items)  # Assume 0.5kg per item
        if total_weight == 0:
            total_weight = 1.0  # Minimum weight
        package_value = order.subtotal
        
        # Build items list in Shipment API format
        shipment_items = []
        for item in order.items:
            product = item.product if hasattr(item, 'product') and item.product else None
            # Try to convert productId to int, but keep as string if conversion fails
            try:
                product_id_int = int(item.product_id) if item.product_id.isdigit() else 0
            except (ValueError, AttributeError):
                product_id_int = 0
                logger.warning(f"[SHIPMENT API] Could not convert productId {item.product_id} to int, using 0")
            
            item_data = {
                "productId": product_id_int,
                "productName": product.name if product else "Unknown Product",
                "productSku": product.id if product else item.product_id,  # Use product ID as SKU
                "quantity": item.quantity,
                "unitPrice": float(item.unit_price),
            }
            shipment_items.append(item_data)
            logger.debug(f"[SHIPMENT API] Added item: {json.dumps(item_data, default=str)}")
        
        # Build shipment data in the exact format expected by Shipment API
        # Parse sender address (use same logic as receiver, or use receiver address)
        sender_city, sender_district, sender_ward = _parse_address(sender_address)
        
        # Helper function to convert datetime to ISO format string or None
        def datetime_to_iso(dt) -> Optional[str]:
            """Convert datetime to ISO format string, return None if datetime is None."""
            return dt.isoformat() if dt else None
        
        # Build shipment data matching the exact API format
        shipment_data = {
            "orderCode": order.order_code,
            # Sender information (using customer info as sender)
            "senderName": order.customer_name or "",
            "senderPhone": order.customer_phone or "",
            "senderAddress": sender_address or "",
            "senderCity": sender_city or "",
            "senderDistrict": sender_district or "",
            "senderWard": sender_ward or "",
            # Receiver information - use customer info as default if receiver info is not available
            "receiverName": receiver_name or "",
            "receiverPhone": receiver_phone or "",
            "receiverAddress": receiver_address_str or "",
            "receiverCity": receiver_city or "",
            "receiverDistrict": receiver_district or "",
            "receiverWard": receiver_ward or "",
            # Package information
            "packageWeight": float(total_weight),
            "packageLength": 10.0,  # Default values, should be calculated or provided
            "packageWidth": 10.0,
            "packageHeight": 10.0,
            "packageValue": float(package_value),
            "packageDescription": ", ".join([f"{item.product.name if item.product else 'Item'} x{item.quantity}" for item in order.items]),
            # Shipping details
            "shippingFee": float(order.shipping_fee),
            "codAmount": float(order.total_amount) if order.payment_method == "COD" else 0.0,
            # Time information - ISO format strings or None
            "estimatedPickupTime": None,  # Not available in current model
            "estimatedDeliveryTime": datetime_to_iso(order.estimated_delivery_time),
            "actualPickupTime": None,  # Not available in current model
            "actualDeliveryTime": datetime_to_iso(order.delivered_at),
            # Carrier and service
            "carrierCode": "",  # Not available in current model
            "serviceType": "STANDARD",  # Default value
            "createdBy": order.customer_id or "",  # Use customer ID as creator, empty string if empty
            # Items
            "items": shipment_items,
        }
        
        # Log the data being sent (for debugging)
        logger.info(f"[SHIPMENT API] Sending order {order.order_code} to {url}")
        logger.debug(f"[SHIPMENT API] Request payload: {json.dumps(shipment_data, indent=2, default=str)}")
        
        # Send to shipment API
        with httpx.Client(timeout=30.0) as client:
            logger.info(f"[SHIPMENT API] Making POST request to {url}")
            response = client.post(url, json=shipment_data)
            
            logger.info(
                f"[SHIPMENT API] Response status: {response.status_code} for order {order.order_code}"
            )
            logger.debug(f"[SHIPMENT API] Response headers: {dict(response.headers)}")
            logger.debug(f"[SHIPMENT API] Response body: {response.text[:500]}")  # First 500 chars
            
            if response.status_code in (200, 201):
                try:
                    response_data = response.json()
                    logger.info(
                        f"[SHIPMENT API] Order {order.order_code} sent successfully. "
                        f"Status: {response.status_code}, Response: {json.dumps(response_data, indent=2, default=str)}"
                    )
                    return response_data
                except Exception as json_error:
                    logger.warning(
                        f"[SHIPMENT API] Success status {response.status_code} but failed to parse JSON: {str(json_error)}. "
                        f"Response text: {response.text[:200]}"
                    )
                    # Return a success indicator even if JSON parsing fails
                    return {"status": "success", "status_code": response.status_code}
            else:
                error_msg = (
                    f"[SHIPMENT API] Failed to send order {order.order_code}: "
                    f"Status {response.status_code}, Response: {response.text}"
                )
                logger.error(error_msg)
                return None
                
    except httpx.TimeoutException as e:
        error_msg = f"[SHIPMENT API] Timeout while sending order {order.order_code}: {str(e)}"
        logger.error(error_msg)
        return None
    except httpx.RequestError as e:
        error_msg = f"[SHIPMENT API] Request error while sending order {order.order_code}: {str(e)}"
        logger.error(error_msg)
        logger.debug(f"[SHIPMENT API] Request error details: {type(e).__name__}: {str(e)}", exc_info=True)
        return None
    except Exception as e:
        error_msg = f"[SHIPMENT API] Unexpected error sending order {order.order_code}: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return None


def update_shipment_status(order_code: str, status: str) -> bool:
    """
    Update shipment status via external API.
    
    Args:
        order_code: Order code to update
        status: New status value (orderStatus)
        
    Returns:
        True if successful, False otherwise
    """
    url = f"{SHIPMENT_API_BASE_URL}api/shipments/{order_code}/status"
    
    try:
        logger.info(f"[SHIPMENT API] Updating status for order {order_code} to {status}")
        
        # Prepare request body
        request_body = {"status": status}
        
        logger.debug(f"[SHIPMENT API] Request URL: {url}")
        logger.debug(f"[SHIPMENT API] Request body: {json.dumps(request_body)}")
        
        # Send PUT request to shipment API
        with httpx.Client(timeout=30.0) as client:
            logger.info(f"[SHIPMENT API] Making PUT request to {url}")
            response = client.put(url, json=request_body)
            
            logger.info(
                f"[SHIPMENT API] Response status: {response.status_code} for order {order_code}"
            )
            logger.debug(f"[SHIPMENT API] Response headers: {dict(response.headers)}")
            logger.debug(f"[SHIPMENT API] Response body: {response.text[:500]}")  # First 500 chars
            
            if response.status_code in (200, 201, 204):
                logger.info(
                    f"[SHIPMENT API] Status updated successfully for order {order_code}. "
                    f"Status: {response.status_code}"
                )
                return True
            else:
                error_msg = (
                    f"[SHIPMENT API] Failed to update status for order {order_code}: "
                    f"Status {response.status_code}, Response: {response.text}"
                )
                logger.error(error_msg)
                return False
                
    except httpx.TimeoutException as e:
        error_msg = f"[SHIPMENT API] Timeout while updating status for order {order_code}: {str(e)}"
        logger.error(error_msg)
        return False
    except httpx.RequestError as e:
        error_msg = f"[SHIPMENT API] Request error while updating status for order {order_code}: {str(e)}"
        logger.error(error_msg)
        logger.debug(f"[SHIPMENT API] Request error details: {type(e).__name__}: {str(e)}", exc_info=True)
        return False
    except Exception as e:
        error_msg = f"[SHIPMENT API] Unexpected error updating status for order {order_code}: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return False

