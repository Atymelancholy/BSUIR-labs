# opencv.pri - Final working configuration
win32 {
    OPENCV_SRC = C:/Users/atyme/opencv
    OPENCV_BUILD = C:/Users/atyme/opencv/build

    INCLUDEPATH += $$OPENCV_SRC/include
    INCLUDEPATH += $$OPENCV_SRC/modules/core/include
    INCLUDEPATH += $$OPENCV_SRC/modules/imgproc/include
    INCLUDEPATH += $$OPENCV_SRC/modules/highgui/include
    INCLUDEPATH += $$OPENCV_SRC/modules/imgcodecs/include
    INCLUDEPATH += $$OPENCV_SRC/modules/videoio/include

    LIBS += -L$$OPENCV_BUILD/lib
    LIBS += -L$$OPENCV_BUILD/bin

    LIBS += -lopencv_core4130
    LIBS += -lopencv_imgproc4130
    LIBS += -lopencv_highgui4130
    LIBS += -lopencv_imgcodecs4130
    LIBS += -lopencv_videoio4130
}
