"""
API Documentation endpoint
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny


class APIDocumentationView(APIView):
    """
    Comprehensive API documentation for Kikapu Platform
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        documentation = {
            "api_info": {
                "name": "Kikapu Platform API",
                "version": "1.0.0",
                "description": "Agricultural supply chain management platform API",
                "base_url": "/api/v1/",
                "authentication": "JWT Bearer Token",
                "rate_limits": {
                    "anonymous": "100 requests/hour",
                    "authenticated": "1000 requests/hour",
                    "payments": "10 requests/minute"
                }
            },
            
            "authentication": {
                "description": "JWT-based authentication system",
                "endpoints": {
                    "POST /auth/register/": {
                        "description": "Register new user account",
                        "public": True,
                        "required_fields": ["email", "username", "phone_number", "user_type", "password"],
                        "user_types": ["farmer", "buyer", "processor", "retailer", "logistics"]
                    },
                    "POST /auth/login/": {
                        "description": "Login and get JWT tokens",
                        "public": True,
                        "required_fields": ["email", "password"],
                        "returns": ["access_token", "refresh_token", "user_info"]
                    },
                    "POST /auth/refresh/": {
                        "description": "Refresh access token",
                        "public": True,
                        "required_fields": ["refresh"]
                    },
                    "POST /auth/logout/": {
                        "description": "Logout and blacklist tokens",
                        "auth_required": True
                    },
                    "GET /auth/profile/": {
                        "description": "Get user profile",
                        "auth_required": True
                    },
                    "PATCH /auth/profile/": {
                        "description": "Update user profile",
                        "auth_required": True
                    },
                    "POST /auth/change-password/": {
                        "description": "Change user password",
                        "auth_required": True,
                        "required_fields": ["old_password", "new_password", "new_password_confirm"]
                    },
                    "POST /auth/verify-email/": {
                        "description": "Verify email address",
                        "public": True,
                        "required_fields": ["verification_token"]
                    },
                    "POST /auth/verify-phone/": {
                        "description": "Verify phone number with SMS code",
                        "auth_required": True,
                        "required_fields": ["verification_code"]
                    }
                }
            },
            
            "products": {
                "description": "Product management and catalog",
                "endpoints": {
                    "GET /products/": {
                        "description": "List products with filtering and search",
                        "public": True,
                        "filters": ["category", "product_type", "min_price", "max_price", "location", "in_stock", "featured"],
                        "search": "name, description, tags, location",
                        "ordering": ["name", "price", "created_at", "rating"]
                    },
                    "POST /products/": {
                        "description": "Create new product",
                        "auth_required": True,
                        "user_types": ["farmer", "processor", "retailer"],
                        "required_fields": ["name", "description", "category", "price", "stock_quantity"]
                    },
                    "GET /products/{id}/": {
                        "description": "Get product details",
                        "public": True
                    },
                    "PUT /products/{id}/": {
                        "description": "Update product",
                        "auth_required": True,
                        "permissions": "Owner or admin"
                    },
                    "GET /products/search/": {
                        "description": "Advanced product search",
                        "public": True,
                        "parameters": ["q", "category", "product_type", "quality_grade", "price_range", "location"]
                    },
                    "GET /products/featured/": {
                        "description": "Get featured products",
                        "public": True
                    },
                    "POST /products/{id}/update_stock/": {
                        "description": "Update product stock",
                        "auth_required": True,
                        "permissions": "Owner or admin",
                        "required_fields": ["quantity"]
                    }
                }
            },
            
            "orders": {
                "description": "Order management and processing",
                "endpoints": {
                    "GET /orders/": {
                        "description": "List user's orders",
                        "auth_required": True,
                        "filters": ["order_status", "payment_status", "date_range"]
                    },
                    "POST /orders/": {
                        "description": "Create new order",
                        "auth_required": True,
                        "required_fields": ["seller", "items", "delivery_method"],
                        "optional_fields": ["billing_address", "shipping_address", "notes"]
                    },
                    "GET /orders/{id}/": {
                        "description": "Get order details",
                        "auth_required": True,
                        "permissions": "Buyer, seller, or admin"
                    },
                    "POST /orders/{id}/update_status/": {
                        "description": "Update order status",
                        "auth_required": True,
                        "permissions": "Seller or admin",
                        "required_fields": ["new_status"],
                        "allowed_transitions": {
                            "pending": ["confirmed", "cancelled"],
                            "confirmed": ["processing", "cancelled"],
                            "processing": ["shipped", "cancelled"],
                            "shipped": ["delivered"]
                        }
                    },
                    "POST /orders/{id}/cancel/": {
                        "description": "Cancel order",
                        "auth_required": True,
                        "permissions": "Buyer or admin",
                        "optional_fields": ["reason"]
                    },
                    "POST /orders/calculate_summary/": {
                        "description": "Calculate order total before placing",
                        "auth_required": True,
                        "required_fields": ["items"],
                        "optional_fields": ["discount_code"]
                    },
                    "GET /orders/my_orders/": {
                        "description": "Get current user's orders",
                        "auth_required": True,
                        "parameters": ["status", "limit"]
                    },
                    "GET /orders/statistics/": {
                        "description": "Get order statistics",
                        "auth_required": True,
                        "parameters": ["date_from", "date_to"]
                    }
                }
            },
            
            "payments": {
                "description": "Payment processing and management",
                "endpoints": {
                    "GET /payments/methods/": {
                        "description": "List available payment methods",
                        "public": True
                    },
                    "POST /payments/process/": {
                        "description": "Process payment for order",
                        "auth_required": True,
                        "required_fields": ["order_id", "payment_method_id"],
                        "optional_fields": ["payment_account_id"],
                        "returns": ["payment_id", "payment_url", "instructions"]
                    },
                    "GET /payments/{payment_id}/status/": {
                        "description": "Check payment status",
                        "auth_required": True,
                        "permissions": "Payment owner"
                    },
                    "GET /payments/": {
                        "description": "List user's payments",
                        "auth_required": True,
                        "parameters": ["limit"]
                    },
                    "POST /payments/{payment_id}/refund/": {
                        "description": "Request payment refund",
                        "auth_required": True,
                        "permissions": "Payment owner",
                        "required_fields": ["refund_reason"],
                        "optional_fields": ["refund_amount", "reason_description"]
                    },
                    "GET /payments/accounts/": {
                        "description": "List user's payment accounts",
                        "auth_required": True
                    },
                    "POST /payments/accounts/create/": {
                        "description": "Add payment account",
                        "auth_required": True,
                        "required_fields": ["payment_method", "account_name", "account_number"]
                    }
                }
            },
            
            "response_formats": {
                "success_response": {
                    "structure": "Direct data or {data: ..., count: ..., next: ..., previous: ...} for paginated",
                    "status_codes": [200, 201]
                },
                "error_response": {
                    "structure": {
                        "error": "Error message",
                        "code": "ERROR_CODE",
                        "details": {}
                    },
                    "status_codes": [400, 401, 403, 404, 422, 500]
                },
                "validation_errors": {
                    "structure": {
                        "field_name": ["Error message 1", "Error message 2"]
                    },
                    "status_code": 400
                }
            },
            
            "common_parameters": {
                "pagination": {
                    "page": "Page number (default: 1)",
                    "page_size": "Items per page (default: 20, max: 100)"
                },
                "filtering": {
                    "search": "Text search across relevant fields",
                    "ordering": "Field to sort by (prefix with - for descending)"
                },
                "date_filtering": {
                    "date_from": "Start date (YYYY-MM-DD)",
                    "date_to": "End date (YYYY-MM-DD)"
                }
            },
            
            "authentication_header": {
                "format": "Authorization: Bearer <access_token>",
                "example": "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
            },
            
            "webhook_endpoints": {
                "payment_webhooks": {
                    "url": "/payments/webhooks/{provider}/",
                    "method": "POST",
                    "providers": ["taka-bank", "mpesa", "tigopesa"],
                    "security": "HMAC signature verification"
                }
            },
            
            "development_info": {
                "base_url_dev": "http://127.0.0.1:8000/api/v1/",
                "admin_interface": "http://127.0.0.1:8000/admin/",
                "test_users": {
                    "farmer": "farmer@test.com / testpass123",
                    "buyer": "buyer@test.com / testpass123"
                },
                "sample_products": "Created via management command: python manage.py create_test_data"
            }
        }
        
        return Response(documentation)