import test_detection
import test_detection_id
import test_detections
import test_stream

def main():
    ids = test_detections.run_test()
    print(f"Ids: {ids}")
    for id in ids:
        test_detection_id.run_test(id=id)
        print(f"Runnning /detections/{id} test...")
#    test_stream.run_test()

if __name__ == "__main__":
    main()
