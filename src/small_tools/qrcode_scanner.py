import cv2
import numpy as np

qr_detector = cv2.QRCodeDetector()

def scan_qrcode_from_image(image_path: str|bytes) -> str | None:
    """Scan a QR code from an image file.

    Args:
        image_path (str|bytes): The path to the image file or the image data in bytes.

    Returns:
        str | None: The decoded text from the QR code, or None if no QR code is found.
    """
    if isinstance(image_path, str):
        image = cv2.imread(image_path)
    elif isinstance(image_path, bytes):
        nparr = np.frombuffer(image_path, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    else:
        raise TypeError("image_path must be a string or bytes.")

    if image is None:
        raise ValueError("Could not load image from the provided path or data.")

    data, points, _ = qr_detector.detectAndDecode(image)

    if points is not None and data:
        return data
    else:
        return None

if __name__ == "__main__":
    import sys
    if len(sys.argv)==2:
        result = scan_qrcode_from_image(sys.argv[1])
        if result is not None:
            print("QR Code Data:", result)
        else:
            print("No QR code found.")
    else:
        while True:
            image_path = input("Enter the path to the image file (or 'exit' to quit): ")
            if image_path.lower() == 'exit':
                break
            try:
                result = scan_qrcode_from_image(image_path)
                if result is not None:
                    print("QR Code Data:", result)
                else:
                    print("No QR code found.")
            except Exception as e:
                print("Error:", e)
