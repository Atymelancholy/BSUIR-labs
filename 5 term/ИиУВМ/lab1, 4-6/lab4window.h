#ifndef LAB4WINDOW_H
#define LAB4WINDOW_H

#include <QMainWindow>
#include <QSystemTrayIcon>
#include <QLabel>
#include <QTimer>
#include <QPoint>
#include <QSize>
#include <QVector>
#include <QPair>
#include <atomic>
#include <thread>
#include <chrono>
#include "characteranimation.h"

#include <opencv2/core.hpp>
#include <opencv2/imgproc.hpp>
#include <opencv2/highgui.hpp>
#include <opencv2/imgcodecs.hpp>
#include <opencv2/videoio.hpp>

namespace Ui {
class Lab4Window;
}

struct CameraInfo {
    QString name;
    QString devicePath;
    QString description;
    QVector<QPair<QString, QString>> capabilities;
};

class Lab4Window : public QMainWindow
{
    Q_OBJECT

public:
    explicit Lab4Window(QWidget *parent = nullptr);
    ~Lab4Window();

signals:
    void backToMain();

private slots:
    void onTakePhotoClicked();
    void onRecordVideoClicked();
    void onCameraInfoClicked();
    void onToggleSecretClicked();
    void onBackClicked();
    void trayIconActivated(QSystemTrayIcon::ActivationReason reason);
    void checkCameraStatus();

protected:
    bool nativeEvent(const QByteArray &eventType, void *message, long long *result) override;
    void closeEvent(QCloseEvent *event) override;
    void resizeEvent(QResizeEvent *event) override;
    void showEvent(QShowEvent *event) override;

private:
    static const int HOTKEY_SHOW = 1;
    static const int HOTKEY_PHOTO = 2;
    static const int HOTKEY_VIDEO = 3;
    static const int DEFAULT_CAMERA_ID = 0;
    static const int DEFAULT_WIDTH = 640;
    static const int DEFAULT_HEIGHT = 480;
    static const double DEFAULT_FPS;

    Ui::Lab4Window *ui;
    QSystemTrayIcon *m_trayIcon;
    CharacterAnimation *m_characterAnimation;
    CharacterAnimation *m_cameraAnimation;
    QTimer *m_cameraCheckTimer;

    std::atomic<bool> m_isSecretMode;
    std::atomic<bool> m_isRecording;
    std::atomic<bool> m_stopRecordingRequested;
    std::atomic<bool> m_cameraActive;

    QPoint m_savedPosition;
    QSize m_savedSize;
    bool m_isMaximized;

    std::thread* m_recordThread;
    cv::VideoCapture* m_videoCapture;
    cv::VideoWriter* m_videoWriter;

    void initializeUI();
    void setupConnections();
    void applyStyles();
    void setupAnimation();
    void updateAnimationPosition();
    void setupCameraAnimation();
    void updateCameraAnimationPosition();
    void showCameraAnimation(bool show);
    void capturePhoto();
    void recordVideo(int seconds, const QString &filename = "");
    void startVideoRecording();
    void stopVideoRecording();
    void videoRecordingThread();
    bool initializeCamera(cv::VideoCapture &camera);
    bool initializeVideoWriter(cv::VideoWriter &writer, const cv::VideoCapture &camera, const QString &filename);
    void printCameraInfo();
    bool isCameraInUse();
    QVector<CameraInfo> getCameraInfoLowLevel();
    QVector<CameraInfo> getDemoCameraData();
    QString getDefaultCameraInfo();
    void toggleSecretMode(bool enable);
    void registerHotkey();
    void unregisterHotkey();
    void startCameraAnimation();
    void stopCameraAnimation();
    void centerWindow();
    void logMessage(const QString &message);
    QString generateTimestamp() const;
    QString generateFilename(const QString &prefix, const QString &extension) const;
};

#endif
