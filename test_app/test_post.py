import test_detection, \
test_detection_id, \
test_detections, \
test_stream, \
test_frames, \
test_frame_id

def main():
    ids = test_frames.run_test()
    print(f"Ids: {ids}")
    for id in ids:
        test_frame_id.run_test(id=id)
        print(f"Runnning /frame/{id} test...")
#    test_stream.run_test()

if __name__ == "__main__":
    main()
