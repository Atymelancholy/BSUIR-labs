#ifndef LAB4WINDOW_H
#define LAB4WINDOW_H

#include <QMainWindow>
#include <QSystemTrayIcon>
#include <QLabel>
#include <QTimer>
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
    // Константы
    static const int HOTKEY_SHOW = 1;
    static const int HOTKEY_PHOTO = 2;
    static const int HOTKEY_VIDEO = 3;
    static const int DEFAULT_CAMERA_ID = 0;
    static const int DEFAULT_WIDTH = 640;
    static const int DEFAULT_HEIGHT = 480;
    static const double DEFAULT_FPS;

    // UI компоненты
    Ui::Lab4Window *ui;
    QSystemTrayIcon *m_trayIcon;
    CharacterAnimation *m_characterAnimation;
    QTimer *m_cameraCheckTimer;

    // Состояние приложения
    std::atomic<bool> m_isSecretMode;
    std::atomic<bool> m_isRecording;
    std::atomic<bool> m_stopRecordingRequested;
    std::atomic<bool> m_cameraActive;

    // Потоки и ресурсы
    std::thread* m_recordThread;
    cv::VideoCapture* m_videoCapture;
    cv::VideoWriter* m_videoWriter;

    // Основные методы
    void initializeUI();
    void setupConnections();
    void applyStyles();
    void setupAnimation();
    void updateAnimationPosition();

    // Методы работы с камерой
    void capturePhoto();
    void recordVideo(int seconds, const QString &filename = "");
    void startVideoRecording();
    void stopVideoRecording();
    void videoRecordingThread();

    // Методы управления камерой
    bool initializeCamera(cv::VideoCapture &camera);
    bool initializeVideoWriter(cv::VideoWriter &writer, const cv::VideoCapture &camera, const QString &filename);
    void printCameraInfo();
    bool isCameraInUse();

    // Методы скрытого режима
    void toggleSecretMode(bool enable);
    void registerHotkey();
    void unregisterHotkey();

    // Методы анимации
    void startCameraAnimation();
    void stopCameraAnimation();

    // Вспомогательные методы
    void logMessage(const QString &message);
    QString generateTimestamp() const;
    QString generateFilename(const QString &prefix, const QString &extension) const;
};

#endif // LAB4WINDOW_H
