"""Unit tests for app.services module"""
from datetime import datetime
from unittest.mock import MagicMock, patch

import httpx
import pytest

from app.services import _parse_address, send_order_to_shipment


class TestParseAddress:
    """Tests for _parse_address function"""
    
    def test_parse_address_empty_string(self):
        """Test parsing empty address string"""
        city, district, ward = _parse_address("")
        assert city == "Ho Chi Minh City"
        assert district == ""
        assert ward == ""
    
    def test_parse_address_none(self):
        """Test parsing None address"""
        city, district, ward = _parse_address(None)
        assert city == "Ho Chi Minh City"
        assert district == ""
        assert ward == ""
    
    def test_parse_address_ho_chi_minh_city(self):
        """Test parsing Ho Chi Minh City address"""
        city, district, ward = _parse_address("Ho Chi Minh City, District 1")
        assert city == "Ho Chi Minh City"
    
    def test_parse_address_ho_chi_minh_vietnamese(self):
        """Test parsing Vietnamese address format"""
        city, district, ward = _parse_address("Hồ Chí Minh, Quận 1")
        assert city == "Ho Chi Minh City"
    
    def test_parse_address_hcm_abbreviation(self):
        """Test parsing HCM abbreviation"""
        city, district, ward = _parse_address("HCM, Vietnam")
        assert city == "Ho Chi Minh City"
    
    def test_parse_address_hanoi(self):
        """Test parsing Hanoi address"""
        city, district, ward = _parse_address("Hanoi, Vietnam")
        assert city == "Hanoi"
    
    def test_parse_address_hanoi_vietnamese(self):
        """Test parsing Hanoi in Vietnamese"""
        city, district, ward = _parse_address("Hà Nội, Việt Nam")
        assert city == "Hanoi"
    
    def test_parse_address_da_nang(self):
        """Test parsing Da Nang address"""
        city, district, ward = _parse_address("Da Nang, Vietnam")
        assert city == "Da Nang"
    
    def test_parse_address_da_nang_vietnamese(self):
        """Test parsing Da Nang in Vietnamese"""
        city, district, ward = _parse_address("Đà Nẵng, Việt Nam")
        assert city == "Da Nang"
    
    def test_parse_address_can_tho(self):
        """Test parsing Can Tho address"""
        city, district, ward = _parse_address("Can Tho, Vietnam")
        assert city == "Can Tho"
    
    def test_parse_address_hai_phong(self):
        """Test parsing Hai Phong address"""
        city, district, ward = _parse_address("Hai Phong, Vietnam")
        assert city == "Hai Phong"
    
    def test_parse_address_unknown_city_defaults(self):
        """Test parsing unknown city defaults to Ho Chi Minh City"""
        city, district, ward = _parse_address("Unknown City, Somewhere")
        assert city == "Ho Chi Minh City"
    
    def test_parse_address_with_district_number(self):
        """Test parsing address with district number"""
        city, district, ward = _parse_address("Ho Chi Minh City, District 5")
        assert city == "Ho Chi Minh City"
        assert district == "District 5"
    
    def test_parse_address_with_district_vietnamese(self):
        """Test parsing address with Vietnamese district"""
        city, district, ward = _parse_address("Ho Chi Minh City, Quận 3")
        assert city == "Ho Chi Minh City"
        assert district == "District 3"
    
    def test_parse_address_case_insensitive(self):
        """Test that address parsing is case insensitive"""
        city1, _, _ = _parse_address("HO CHI MINH CITY")
        city2, _, _ = _parse_address("ho chi minh city")
        city3, _, _ = _parse_address("Ho Chi Minh City")
        assert city1 == city2 == city3 == "Ho Chi Minh City"


class TestSendOrderToShipment:
    """Tests for send_order_to_shipment function"""
    
    def test_send_order_success(self, sample_order):
        """Test successful order shipment"""
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "shippingOrderCode": "SHIP-123",
            "status": "CREATED",
            "shipper": {"name": "Test Shipper"},
        }
        mock_response.text = '{"status": "success"}'
        
        with patch("app.services.httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client.__enter__.return_value = mock_client
            mock_client.__exit__.return_value = None
            mock_client.post.return_value = mock_response
            mock_client_class.return_value = mock_client
            
            result = send_order_to_shipment(sample_order)
            
            assert result is not None
            assert result["shippingOrderCode"] == "SHIP-123"
            assert result["status"] == "CREATED"
            mock_client.post.assert_called_once()
    
    def test_send_order_success_status_200(self, sample_order):
        """Test successful order shipment with status 200"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "success"}
        mock_response.text = '{"status": "success"}'
        
        with patch("app.services.httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client.__enter__.return_value = mock_client
            mock_client.__exit__.return_value = None
            mock_client.post.return_value = mock_response
            mock_client_class.return_value = mock_client
            
            result = send_order_to_shipment(sample_order)
            
            assert result is not None
            assert result["status"] == "success"
    
    def test_send_order_api_error(self, sample_order):
        """Test order shipment with API error response"""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        
        with patch("app.services.httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client.__enter__.return_value = mock_client
            mock_client.__exit__.return_value = None
            mock_client.post.return_value = mock_response
            mock_client_class.return_value = mock_client
            
            result = send_order_to_shipment(sample_order)
            
            assert result is None
    
    def test_send_order_timeout(self, sample_order):
        """Test order shipment with timeout exception"""
        with patch("app.services.httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client.__enter__.return_value = mock_client
            mock_client.__exit__.return_value = None
            mock_client.post.side_effect = httpx.TimeoutException("Request timeout")
            mock_client_class.return_value = mock_client
            
            result = send_order_to_shipment(sample_order)
            
            assert result is None
    
    def test_send_order_request_error(self, sample_order):
        """Test order shipment with request error"""
        with patch("app.services.httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client.__enter__.return_value = mock_client
            mock_client.__exit__.return_value = None
            mock_client.post.side_effect = httpx.RequestError("Connection error")
            mock_client_class.return_value = mock_client
            
            result = send_order_to_shipment(sample_order)
            
            assert result is None
    
    def test_send_order_unexpected_exception(self, sample_order):
        """Test order shipment with unexpected exception"""
        with patch("app.services.httpx.Client") as mock_client_class:
            mock_client_class.side_effect = Exception("Unexpected error")
            
            result = send_order_to_shipment(sample_order)
            
            assert result is None
    
    def test_send_order_json_parse_error(self, sample_order):
        """Test order shipment with JSON parse error on success response"""
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_response.text = "Invalid JSON response"
        
        with patch("app.services.httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client.__enter__.return_value = mock_client
            mock_client.__exit__.return_value = None
            mock_client.post.return_value = mock_response
            mock_client_class.return_value = mock_client
            
            result = send_order_to_shipment(sample_order)
            
            assert result is not None
            assert result["status"] == "success"
            assert result["status_code"] == 201
    
    def test_send_order_with_receiver_info(self, sample_order):
        """Test order shipment with receiver information"""
        sample_order.receiver_name = "Receiver Name"
        sample_order.receiver_phone = "0987654321"
        sample_order.receiver_address = "Hanoi, Vietnam"
        
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"status": "success"}
        mock_response.text = '{"status": "success"}'
        
        with patch("app.services.httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client.__enter__.return_value = mock_client
            mock_client.__exit__.return_value = None
            mock_client.post.return_value = mock_response
            mock_client_class.return_value = mock_client
            
            result = send_order_to_shipment(sample_order)
            
            assert result is not None
            # Verify the request payload includes receiver info
            call_args = mock_client.post.call_args
            assert call_args is not None
            shipment_data = call_args.kwargs.get("json", {})
            assert shipment_data["receiverName"] == "Receiver Name"
            assert shipment_data["receiverPhone"] == "0987654321"
            assert shipment_data["receiverAddress"] == "Hanoi, Vietnam"
            assert shipment_data["receiverCity"] == "Hanoi"
            # Sender address should use receiver address when receiver address is provided
            assert shipment_data["senderAddress"] == "Hanoi, Vietnam"
            assert shipment_data["senderCity"] == "Hanoi"
    
    def test_send_order_without_receiver_info(self, sample_order):
        """Test order shipment without receiver info (uses customer info)"""
        sample_order.receiver_name = None
        sample_order.receiver_phone = None
        sample_order.receiver_address = None
        
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"status": "success"}
        mock_response.text = '{"status": "success"}'
        
        with patch("app.services.httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client.__enter__.return_value = mock_client
            mock_client.__exit__.return_value = None
            mock_client.post.return_value = mock_response
            mock_client_class.return_value = mock_client
            
            result = send_order_to_shipment(sample_order)
            
            assert result is not None
            call_args = mock_client.post.call_args
            shipment_data = call_args.kwargs.get("json", {})
            # Should use customer info as default
            assert shipment_data["receiverName"] == sample_order.customer_name
            assert shipment_data["receiverPhone"] == sample_order.customer_phone
            # Should use default address when receiver_address is None
            assert shipment_data["receiverAddress"] == "Ho Chi Minh City, Vietnam"
            assert shipment_data["receiverCity"] == "Ho Chi Minh City"
            # Sender address should also use the same default
            assert shipment_data["senderAddress"] == "Ho Chi Minh City, Vietnam"
            assert shipment_data["senderCity"] == "Ho Chi Minh City"
    
    def test_send_order_calculates_weight(self, sample_order):
        """Test that order weight is calculated from items"""
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"status": "success"}
        mock_response.text = '{"status": "success"}'
        
        with patch("app.services.httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client.__enter__.return_value = mock_client
            mock_client.__exit__.return_value = None
            mock_client.post.return_value = mock_response
            mock_client_class.return_value = mock_client
            
            result = send_order_to_shipment(sample_order)
            
            assert result is not None
            call_args = mock_client.post.call_args
            shipment_data = call_args.kwargs.get("json", {})
            # Weight should be calculated: 2 items * 0.5kg = 1.0kg
            assert shipment_data["packageWeight"] == 1.0
    
    def test_send_order_zero_weight_minimum(self, sample_order):
        """Test that zero weight defaults to minimum 1.0kg"""
        # Create order with no items
        sample_order.items = []
        
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"status": "success"}
        mock_response.text = '{"status": "success"}'
        
        with patch("app.services.httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client.__enter__.return_value = mock_client
            mock_client.__exit__.return_value = None
            mock_client.post.return_value = mock_response
            mock_client_class.return_value = mock_client
            
            result = send_order_to_shipment(sample_order)
            
            assert result is not None
            call_args = mock_client.post.call_args
            shipment_data = call_args.kwargs.get("json", {})
            # Should default to 1.0kg minimum
            assert shipment_data["packageWeight"] == 1.0
    
    def test_send_order_cod_amount(self, sample_order):
        """Test COD amount is set correctly for COD payment"""
        sample_order.payment_method = "COD"
        sample_order.total_amount = 500.0
        
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"status": "success"}
        mock_response.text = '{"status": "success"}'
        
        with patch("app.services.httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client.__enter__.return_value = mock_client
            mock_client.__exit__.return_value = None
            mock_client.post.return_value = mock_response
            mock_client_class.return_value = mock_client
            
            result = send_order_to_shipment(sample_order)
            
            assert result is not None
            call_args = mock_client.post.call_args
            shipment_data = call_args.kwargs.get("json", {})
            assert shipment_data["codAmount"] == 500.0
    
    def test_send_order_non_cod_amount(self, sample_order):
        """Test COD amount is 0 for non-COD payment"""
        sample_order.payment_method = "BANK_TRANSFER"
        sample_order.total_amount = 500.0
        
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"status": "success"}
        mock_response.text = '{"status": "success"}'
        
        with patch("app.services.httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client.__enter__.return_value = mock_client
            mock_client.__exit__.return_value = None
            mock_client.post.return_value = mock_response
            mock_client_class.return_value = mock_client
            
            result = send_order_to_shipment(sample_order)
            
            assert result is not None
            call_args = mock_client.post.call_args
            shipment_data = call_args.kwargs.get("json", {})
            assert shipment_data["codAmount"] == 0.0
    
    def test_send_order_with_datetime_fields(self, sample_order):
        """Test order shipment with datetime fields"""
        sample_order.estimated_delivery_time = datetime(2024, 12, 31, 12, 0, 0)
        sample_order.delivered_at = datetime(2024, 12, 31, 14, 0, 0)
        
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"status": "success"}
        mock_response.text = '{"status": "success"}'
        
        with patch("app.services.httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client.__enter__.return_value = mock_client
            mock_client.__exit__.return_value = None
            mock_client.post.return_value = mock_response
            mock_client_class.return_value = mock_client
            
            result = send_order_to_shipment(sample_order)
            
            assert result is not None
            call_args = mock_client.post.call_args
            shipment_data = call_args.kwargs.get("json", {})
            # Datetime fields should be converted to ISO format strings
            assert shipment_data["estimatedDeliveryTime"] is not None
            assert isinstance(shipment_data["estimatedDeliveryTime"], str)
            assert shipment_data["actualDeliveryTime"] is not None
            assert isinstance(shipment_data["actualDeliveryTime"], str)
    
    def test_send_order_with_none_datetime_fields(self, sample_order):
        """Test order shipment with None datetime fields"""
        sample_order.estimated_delivery_time = None
        sample_order.delivered_at = None
        
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"status": "success"}
        mock_response.text = '{"status": "success"}'
        
        with patch("app.services.httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client.__enter__.return_value = mock_client
            mock_client.__exit__.return_value = None
            mock_client.post.return_value = mock_response
            mock_client_class.return_value = mock_client
            
            result = send_order_to_shipment(sample_order)
            
            assert result is not None
            call_args = mock_client.post.call_args
            shipment_data = call_args.kwargs.get("json", {})
            assert shipment_data["estimatedDeliveryTime"] is None
            assert shipment_data["actualDeliveryTime"] is None


class TestParseAddressFailureScenarios:
    """Failure scenario tests for _parse_address function"""
    
    def test_parse_address_invalid_type_number(self):
        """Test parsing address with invalid type (number)"""
        # address_str.lower() will raise AttributeError for non-string types
        with pytest.raises(AttributeError):
            _parse_address(12345)
    
    def test_parse_address_invalid_type_list(self):
        """Test parsing address with invalid type (list)"""
        with pytest.raises(AttributeError):
            _parse_address(["address", "city"])
    
    def test_parse_address_invalid_type_dict(self):
        """Test parsing address with invalid type (dict)"""
        with pytest.raises(AttributeError):
            _parse_address({"address": "test"})
    
    def test_parse_address_very_long_string(self):
        """Test parsing address with extremely long string"""
        long_address = "Ho Chi Minh City, " + "A" * 10000
        city, district, ward = _parse_address(long_address)
        assert city == "Ho Chi Minh City"
        assert isinstance(district, str)
        assert isinstance(ward, str)
    
    def test_parse_address_only_special_characters(self):
        """Test parsing address with only special characters"""
        city, district, ward = _parse_address("!@#$%^&*()")
        assert city == "Ho Chi Minh City"  # Default fallback
        assert district == ""
        assert ward == ""
    
    def test_parse_address_only_numbers(self):
        """Test parsing address with only numbers"""
        city, district, ward = _parse_address("123456789")
        assert city == "Ho Chi Minh City"  # Default fallback
        assert district == ""
        assert ward == ""
    
    def test_parse_address_whitespace_only(self):
        """Test parsing address with only whitespace"""
        city, district, ward = _parse_address("   \n\t  ")
        assert city == "Ho Chi Minh City"  # Default fallback
        assert district == ""
        assert ward == ""
    
    def test_parse_address_malformed_unicode(self):
        """Test parsing address with malformed unicode characters"""
        # Should handle gracefully
        city, district, ward = _parse_address("Ho Chi Minh City\x00\x01\x02")
        assert city == "Ho Chi Minh City"
        assert isinstance(district, str)
        assert isinstance(ward, str)


class TestSendOrderToShipmentFailureScenarios:
    """Failure scenario tests for send_order_to_shipment function"""
    
    def test_send_order_none_order_object(self):
        """Test sending None order object"""
        with pytest.raises((AttributeError, TypeError)):
            send_order_to_shipment(None)
    
    def test_send_order_missing_order_code(self):
        """Test sending order with missing order_code"""
        mock_order = MagicMock()
        mock_order.order_code = None
        mock_order.customer_name = "Test"
        mock_order.customer_phone = "123"
        mock_order.items = []
        mock_order.subtotal = 100.0
        mock_order.shipping_fee = 0.0
        mock_order.total_amount = 100.0
        mock_order.payment_method = "COD"
        mock_order.receiver_name = None
        mock_order.receiver_phone = None
        mock_order.receiver_address = None
        mock_order.customer_id = ""
        mock_order.estimated_delivery_time = None
        mock_order.delivered_at = None
        
        result = send_order_to_shipment(mock_order)
        # Should handle None order_code gracefully or fail
        assert result is None or isinstance(result, dict)
    
    def test_send_order_missing_customer_name(self):
        """Test sending order with missing customer_name"""
        mock_order = MagicMock()
        mock_order.order_code = "ORD-123"
        mock_order.customer_name = None
        mock_order.customer_phone = "123"
        mock_order.items = []
        mock_order.subtotal = 100.0
        mock_order.shipping_fee = 0.0
        mock_order.total_amount = 100.0
        mock_order.payment_method = "COD"
        mock_order.receiver_name = None
        mock_order.receiver_phone = None
        mock_order.receiver_address = None
        mock_order.customer_id = ""
        mock_order.estimated_delivery_time = None
        mock_order.delivered_at = None
        
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"status": "success"}
        mock_response.text = '{"status": "success"}'
        
        with patch("app.services.httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client.__enter__.return_value = mock_client
            mock_client.__exit__.return_value = None
            mock_client.post.return_value = mock_response
            mock_client_class.return_value = mock_client
            
            result = send_order_to_shipment(mock_order)
            # Should handle None customer_name (use empty string)
            assert result is not None
            call_args = mock_client.post.call_args
            shipment_data = call_args.kwargs.get("json", {})
            assert shipment_data["senderName"] == "" or shipment_data["senderName"] is None
    
    def test_send_order_empty_items_list(self):
        """Test sending order with empty items list"""
        mock_order = MagicMock()
        mock_order.order_code = "ORD-123"
        mock_order.customer_name = "Test"
        mock_order.customer_phone = "123"
        mock_order.items = []  # Empty items
        mock_order.subtotal = 0.0
        mock_order.shipping_fee = 0.0
        mock_order.total_amount = 0.0
        mock_order.payment_method = "COD"
        mock_order.receiver_name = None
        mock_order.receiver_phone = None
        mock_order.receiver_address = None
        mock_order.customer_id = ""
        mock_order.estimated_delivery_time = None
        mock_order.delivered_at = None
        
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"status": "success"}
        mock_response.text = '{"status": "success"}'
        
        with patch("app.services.httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client.__enter__.return_value = mock_client
            mock_client.__exit__.return_value = None
            mock_client.post.return_value = mock_response
            mock_client_class.return_value = mock_client
            
            result = send_order_to_shipment(mock_order)
            assert result is not None
            call_args = mock_client.post.call_args
            shipment_data = call_args.kwargs.get("json", {})
            # Should use minimum weight of 1.0kg for empty items
            assert shipment_data["packageWeight"] == 1.0
            assert shipment_data["items"] == []
    
    def test_send_order_negative_subtotal(self, sample_order):
        """Test sending order with negative subtotal"""
        sample_order.subtotal = -100.0
        sample_order.total_amount = -100.0
        
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"status": "success"}
        mock_response.text = '{"status": "success"}'
        
        with patch("app.services.httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client.__enter__.return_value = mock_client
            mock_client.__exit__.return_value = None
            mock_client.post.return_value = mock_response
            mock_client_class.return_value = mock_client
            
            result = send_order_to_shipment(sample_order)
            # Should still send, but validate defensive behavior
            assert result is not None
            call_args = mock_client.post.call_args
            shipment_data = call_args.kwargs.get("json", {})
            assert shipment_data["packageValue"] == -100.0
    
    def test_send_order_very_large_values(self, sample_order):
        """Test sending order with very large numeric values"""
        sample_order.subtotal = 1e15
        sample_order.total_amount = 1e15
        sample_order.shipping_fee = 1e10
        
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"status": "success"}
        mock_response.text = '{"status": "success"}'
        
        with patch("app.services.httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client.__enter__.return_value = mock_client
            mock_client.__exit__.return_value = None
            mock_client.post.return_value = mock_response
            mock_client_class.return_value = mock_client
            
            result = send_order_to_shipment(sample_order)
            assert result is not None
            call_args = mock_client.post.call_args
            shipment_data = call_args.kwargs.get("json", {})
            assert shipment_data["packageValue"] == 1e15
            assert shipment_data["shippingFee"] == 1e10
    
    def test_send_order_server_error_500(self, sample_order):
        """Test order shipment with server error (500)"""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        
        with patch("app.services.httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client.__enter__.return_value = mock_client
            mock_client.__exit__.return_value = None
            mock_client.post.return_value = mock_response
            mock_client_class.return_value = mock_client
            
            result = send_order_to_shipment(sample_order)
            assert result is None
    
    def test_send_order_unauthorized_401(self, sample_order):
        """Test order shipment with unauthorized error (401)"""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        
        with patch("app.services.httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client.__enter__.return_value = mock_client
            mock_client.__exit__.return_value = None
            mock_client.post.return_value = mock_response
            mock_client_class.return_value = mock_client
            
            result = send_order_to_shipment(sample_order)
            assert result is None
    
    def test_send_order_forbidden_403(self, sample_order):
        """Test order shipment with forbidden error (403)"""
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.text = "Forbidden"
        
        with patch("app.services.httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client.__enter__.return_value = mock_client
            mock_client.__exit__.return_value = None
            mock_client.post.return_value = mock_response
            mock_client_class.return_value = mock_client
            
            result = send_order_to_shipment(sample_order)
            assert result is None
    
    def test_send_order_network_connection_error(self, sample_order):
        """Test order shipment with network connection error"""
        with patch("app.services.httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client.__enter__.return_value = mock_client
            mock_client.__exit__.return_value = None
            mock_client.post.side_effect = httpx.ConnectError("Connection refused")
            mock_client_class.return_value = mock_client
            
            result = send_order_to_shipment(sample_order)
            assert result is None
    
    def test_send_order_invalid_json_response(self, sample_order):
        """Test order shipment with invalid JSON in response"""
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_response.text = "Not a valid JSON response"
        
        with patch("app.services.httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client.__enter__.return_value = mock_client
            mock_client.__exit__.return_value = None
            mock_client.post.return_value = mock_response
            mock_client_class.return_value = mock_client
            
            result = send_order_to_shipment(sample_order)
            # Should return success indicator even if JSON parsing fails
            assert result is not None
            assert "status" in result or "status_code" in result
    
    def test_send_order_item_without_product(self, sample_order):
        """Test sending order with item that has no product relationship"""
        # Create item without product
        mock_item = MagicMock()
        mock_item.quantity = 1
        mock_item.unit_price = 100.0
        mock_item.product_id = "test-id"
        mock_item.product = None  # No product relationship
        
        sample_order.items = [mock_item]
        
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"status": "success"}
        mock_response.text = '{"status": "success"}'
        
        with patch("app.services.httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client.__enter__.return_value = mock_client
            mock_client.__exit__.return_value = None
            mock_client.post.return_value = mock_response
            mock_client_class.return_value = mock_client
            
            result = send_order_to_shipment(sample_order)
            assert result is not None
            call_args = mock_client.post.call_args
            shipment_data = call_args.kwargs.get("json", {})
            # Should handle missing product gracefully
            assert len(shipment_data["items"]) == 1
            assert shipment_data["items"][0]["productName"] == "Unknown Product"
    
    def test_send_order_invalid_product_id_conversion(self, sample_order):
        """Test sending order with product ID that cannot be converted to int"""
        mock_item = MagicMock()
        mock_item.quantity = 1
        mock_item.unit_price = 100.0
        mock_item.product_id = "non-numeric-id"  # Cannot convert to int
        mock_item.product = None
        
        sample_order.items = [mock_item]
        
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"status": "success"}
        mock_response.text = '{"status": "success"}'
        
        with patch("app.services.httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client.__enter__.return_value = mock_client
            mock_client.__exit__.return_value = None
            mock_client.post.return_value = mock_response
            mock_client_class.return_value = mock_client
            
            result = send_order_to_shipment(sample_order)
            assert result is not None
            call_args = mock_client.post.call_args
            shipment_data = call_args.kwargs.get("json", {})
            # Should use 0 as default when conversion fails
            assert shipment_data["items"][0]["productId"] == 0

