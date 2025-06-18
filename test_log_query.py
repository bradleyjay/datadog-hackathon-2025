#!/usr/bin/env python3

import requests
import json
from datetime import datetime, timedelta

# Configuration
OPSIGHT_BASE_URL = "http://localhost:5000"

def test_health():
    """Test health endpoint"""
    print("Testing health endpoint...")
    try:
        response = requests.get(f"{OPSIGHT_BASE_URL}/health")
        print(f"Health Status: {response.status_code}")
        print(f"Response: {response.json()}")
        print()
        return response.status_code == 200
    except Exception as e:
        print(f"Health check failed: {e}")
        return False

def test_search_logs_default():
    """Test search logs with default parameters (datadog-agent, 1 hour ago, 5-minute window, limit 5)"""
    print("Testing search logs with default parameters...")
    print("Query: 'datadog-agent', Time: 1 hour ago (5-minute window), Limit: 5")
    
    try:
        # Test with no payload (should use defaults)
        response = requests.post(f"{OPSIGHT_BASE_URL}/logs/search", 
                               json={})
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Success: {data['success']}")
            print(f"Query used: {data['query']}")
            print(f"Time range: {data['time_range']['start']} to {data['time_range']['end']}")
            
            logs_data = data['data']
            print(f"Total logs returned: {len(logs_data.get('data', []))}")
            
            # Show sample logs
            if 'data' in logs_data and logs_data['data']:
                print("\nSample logs:")
                for i, log in enumerate(logs_data['data'][:3]):  # Show first 3
                    print(f"  Log {i+1}:")
                    print(f"    Timestamp: {log.get('attributes', {}).get('timestamp', 'N/A')}")
                    print(f"    Message: {log.get('attributes', {}).get('message', 'N/A')[:100]}...")
                    print(f"    Service: {log.get('attributes', {}).get('service', 'N/A')}")
                    print(f"    Status: {log.get('attributes', {}).get('status', 'N/A')}")
                    print()
            else:
                print("No logs found in the specified time range")
        else:
            print(f"Error: {response.text}")
        
        print("-" * 50)
        return response.status_code == 200
        
    except Exception as e:
        print(f"Search logs test failed: {e}")
        print("-" * 50)
        return False

def test_search_logs_custom_limit():
    """Test search logs with custom limit"""
    print("Testing search logs with custom limit...")
    
    payload = {
        "query": "datadog-agent",
        "limit": 10
    }
    
    print(f"Query: {payload['query']}")
    print(f"Limit: {payload['limit']}")
    
    try:
        response = requests.post(f"{OPSIGHT_BASE_URL}/logs/search", 
                               json=payload)
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Success: {data['success']}")
            
            logs_data = data['data']
            print(f"Total logs returned: {len(logs_data.get('data', []))}")
            
            # Show sample logs
            if 'data' in logs_data and logs_data['data']:
                print("\nSample logs:")
                for i, log in enumerate(logs_data['data'][:2]):  # Show first 2
                    print(f"  Log {i+1}:")
                    print(f"    Timestamp: {log.get('attributes', {}).get('timestamp', 'N/A')}")
                    print(f"    Message: {log.get('attributes', {}).get('message', 'N/A')[:100]}...")
                    print(f"    Service: {log.get('attributes', {}).get('service', 'N/A')}")
                    print()
            else:
                print("No logs found in the specified time range")
        else:
            print(f"Error: {response.text}")
        
        print("-" * 50)
        return response.status_code == 200
        
    except Exception as e:
        print(f"Custom limit search test failed: {e}")
        print("-" * 50)
        return False

def test_search_logs_any():
    """Test search logs for any logs (wildcard)"""
    print("Testing search logs for any logs...")
    
    payload = {
        "query": "*",
        "limit": 3
    }
    
    print(f"Query: {payload['query']}")
    print(f"Limit: {payload['limit']}")
    
    try:
        response = requests.post(f"{OPSIGHT_BASE_URL}/logs/search", 
                               json=payload)
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Success: {data['success']}")
            
            logs_data = data['data']
            print(f"Total logs returned: {len(logs_data.get('data', []))}")
            
            # Show sample logs
            if 'data' in logs_data and logs_data['data']:
                print("\nSample logs:")
                for i, log in enumerate(logs_data['data'][:2]):  # Show first 2
                    print(f"  Log {i+1}:")
                    print(f"    Timestamp: {log.get('attributes', {}).get('timestamp', 'N/A')}")
                    print(f"    Message: {log.get('attributes', {}).get('message', 'N/A')[:100]}...")
                    print(f"    Service: {log.get('attributes', {}).get('service', 'N/A')}")
                    print()
            else:
                print("No logs found in the specified time range")
        else:
            print(f"Error: {response.text}")
        
        print("-" * 50)
        return response.status_code == 200
        
    except Exception as e:
        print(f"Wildcard search test failed: {e}")
        print("-" * 50)
        return False

def test_search_logs_specific_service():
    """Test search logs for a specific service"""
    print("Testing search logs for specific service...")
    
    payload = {
        "query": "service:datadog-agent",
        "limit": 5
    }
    
    print(f"Query: {payload['query']}")
    print(f"Limit: {payload['limit']}")
    
    try:
        response = requests.post(f"{OPSIGHT_BASE_URL}/logs/search", 
                               json=payload)
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Success: {data['success']}")
            
            logs_data = data['data']
            print(f"Total logs returned: {len(logs_data.get('data', []))}")
            
            # Show sample logs
            if 'data' in logs_data and logs_data['data']:
                print("\nSample logs:")
                for i, log in enumerate(logs_data['data'][:2]):  # Show first 2
                    print(f"  Log {i+1}:")
                    print(f"    Timestamp: {log.get('attributes', {}).get('timestamp', 'N/A')}")
                    print(f"    Message: {log.get('attributes', {}).get('message', 'N/A')[:100]}...")
                    print(f"    Service: {log.get('attributes', {}).get('service', 'N/A')}")
                    print()
            else:
                print("No logs found in the specified time range")
        else:
            print(f"Error: {response.text}")
        
        print("-" * 50)
        return response.status_code == 200
        
    except Exception as e:
        print(f"Service-specific search test failed: {e}")
        print("-" * 50)
        return False

if __name__ == "__main__":
    print("=== Opsight Log Query Test ===")
    print(f"Test started at: {datetime.utcnow().isoformat()}Z")
    print()
    
    results = []
    
    # Test health endpoint
    results.append(test_health())
    
    # Test default search (datadog-agent, 1 hour ago, 5-minute window)
    results.append(test_search_logs_default())
    
    # Test custom limit
    results.append(test_search_logs_custom_limit())
    
    # Test wildcard search
    results.append(test_search_logs_any())
    
    # Test service-specific search
    results.append(test_search_logs_specific_service())
    
    # Summary
    print("=== Test Summary ===")
    print(f"Tests passed: {sum(results)}/{len(results)}")
    if all(results):
        print("All tests passed! ✅")
    else:
        print("Some tests failed ❌")
        
    print(f"Test completed at: {datetime.utcnow().isoformat()}Z") 