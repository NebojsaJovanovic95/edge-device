import test_detection
import test_detection_id
import test_detections
import test_stream

def main():
    print("Runnning /detect test...")
    id = test_detection.run_test()
    print(f"Runnning /detection/{id} test...")
    test_detection_id.run_test(id=id)
    print("Runnning /detections test...")
    test_detections.run_test()
    print("Runnning /stream test...")
    test_stream.run_test()

if __name__ == "__main__":
    main()