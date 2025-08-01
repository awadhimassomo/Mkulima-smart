#!/bin/bash

# Set base URL
BASE_URL="http://127.0.0.1:8000/api/v1"

echo "Testing Kikapu Platform APIs..."

# Test 1: Health check
echo "1. Testing health check in"
for i in {3..1}; do
  echo " $i,"
  sleep 1
done
echo
curl -s "$BASE_URL/../health/" | python -m json.tool

# Test 2: API root
echo -e "\n2. Testing API root in"
for i in {3..1}; do
  echo " $i,"
  sleep 1
done
echo
curl -s "$BASE_URL/" | python -m json.tool

# Test 3: User registration
echo -e "\n3. Testing user registration in"
for i in {3..1}; do
  echo " $i,"
  sleep 1
done
echo
curl -s -X POST "$BASE_URL/auth/register/" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "testuser2@example.com",
    "username": "testuser",
    "phone_number": "+255623456789",
    "user_type": "buyer",
    "full_name": "Test User",
    "password": "testpass123",
    "password_confirm": "testpass123"
  }' | python -m json.tool

# Test 4: Login
echo -e "\n4. Testing login in"
for i in {3..1}; do
  echo " $i,"
  sleep 1
done
echo
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/login/" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "testuser2@example.com",
    "password": "testpass123"
  }')

echo $LOGIN_RESPONSE | python -m json.tool

# Extract token for authenticated requests
echo -n "   ~ Extracting access token ~"
TOKEN=$(echo $LOGIN_RESPONSE | python -c "import sys, json; print(json.load(sys.stdin)['access'])" 2>/dev/null)

if [ ! -z "$TOKEN" ]; then
  echo -e "\n5. Testing authenticated endpoints..."
  
  # Test profile
  echo "5a. Testing profile in"
  for i in {3..1}; do
    echo " $i,"
    sleep 1
  done
  echo
  curl -s -H "Authorization: Bearer $TOKEN" "$BASE_URL/auth/profile/" | python -m json.tool
  
  # Test products
  echo -e "\n5b. Testing products in"
  for i in {3..1}; do
    echo " $i,"
    sleep 1
  done
  echo
  curl -s "$BASE_URL/products/" | python -m json.tool
  
  # Test categories
  echo -e "\n5c. Testing categories in"
  for i in {3..1}; do
    echo " $i,"
    sleep 1
  done
  echo
  curl -s "$BASE_URL/products/categories/" | python -m json.tool
  
  # Test payment methods
  echo -e "\n5d. Testing payment methods in"
  for i in {3..1}; do
    echo " $i,"
    sleep 1
  done
  echo
  curl -s "$BASE_URL/payments/methods/" | python -m json.tool
else
  echo "Login failed - cannot test authenticated endpoints"
fi

echo -e "\nAPI testing completed!"