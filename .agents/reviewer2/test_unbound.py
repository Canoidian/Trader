import requests
import time

def test_unbound():
    for attempt in range(3):
        # mock 429
        status_code = 429
        if status_code == 429:
            continue
        data = {"result": "success"}
        break
    else:
        pass
    
    print(data)

if __name__ == "__main__":
    test_unbound()
