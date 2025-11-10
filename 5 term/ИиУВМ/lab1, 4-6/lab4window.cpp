#include "lab4window.h"
#include "ui_lab4window.h"

#include <QMessageBox>
#include <QCloseEvent>
#include <QDateTime>
#include <QThread>
#include <QFile>
#include <QScrollBar>
#include <QResizeEvent>
#include <QShowEvent>
#include <QPainter>
#include <QDir>
#include <QScreen>
#include <QGuiApplication>
#include <windows.h>
#include <setupapi.h>

#pragma comment(lib, "setupapi.lib")

using namespace cv;
using namespace std;

const double Lab4Window::DEFAULT_FPS = 25.0;

Lab4Window::Lab4Window(QWidget *parent) :
    QMainWindow(parent),
    ui(new Ui::Lab4Window),
    m_characterAnimation(nullptr),
    m_cameraAnimation(nullptr),
    m_isSecretMode(false),
    m_isRecording(false),
    m_stopRecordingRequested(false),
    m_cameraActive(false),
    m_isMaximized(false),
    m_recordThread(nullptr),
    m_videoCapture(nullptr),
    m_videoWriter(nullptr)
{
    ui->setupUi(this);
    setWindowTitle("Лабораторная работа 4 - Работа с камерой");

    initializeUI();
    setupConnections();
    applyStyles();
    setupAnimation();
    setupCameraAnimation();
    registerHotkey();

    QTimer::singleShot(100, this, &Lab4Window::centerWindow);
}

Lab4Window::~Lab4Window()
{
    if (m_isRecording) {
        stopVideoRecording();
    }
    unregisterHotkey();

    if (m_characterAnimation) delete m_characterAnimation;
    if (m_cameraAnimation) delete m_cameraAnimation;

    delete ui;
}

QVector<CameraInfo> Lab4Window::getCameraInfoLowLevel()
{
    QVector<CameraInfo> cameras;

    HKEY hKey;
    LONG result = RegOpenKeyEx(HKEY_LOCAL_MACHINE,
                               L"SYSTEM\\CurrentControlSet\\Control\\Class\\{6bdd1fc6-810f-11d0-bec7-08002be2092f}",
                               0, KEY_READ, &hKey);

    if (result == ERROR_SUCCESS) {
        DWORD index = 0;
        wchar_t keyName[256];
        DWORD keyNameSize = sizeof(keyName);

        while (RegEnumKeyEx(hKey, index, keyName, &keyNameSize, nullptr, nullptr, nullptr, nullptr) == ERROR_SUCCESS) {
            HKEY hSubKey;
            wchar_t subKeyPath[512];

            swprintf(subKeyPath, 512, L"SYSTEM\\CurrentControlSet\\Control\\Class\\{6bdd1fc6-810f-11d0-bec7-08002be2092f}\\%s", keyName);

            if (RegOpenKeyEx(HKEY_LOCAL_MACHINE, subKeyPath, 0, KEY_READ, &hSubKey) == ERROR_SUCCESS) {
                CameraInfo cameraInfo;

                wchar_t friendlyName[256];
                DWORD friendlyNameSize = sizeof(friendlyName);
                if (RegQueryValueEx(hSubKey, L"FriendlyName", nullptr, nullptr,
                                    (LPBYTE)friendlyName, &friendlyNameSize) == ERROR_SUCCESS) {
                    cameraInfo.name = QString::fromWCharArray(friendlyName);
                }

                wchar_t description[256];
                DWORD descriptionSize = sizeof(description);
                if (RegQueryValueEx(hSubKey, L"DeviceDescription", nullptr, nullptr,
                                    (LPBYTE)description, &descriptionSize) == ERROR_SUCCESS) {
                    cameraInfo.description = QString::fromWCharArray(description);
                }

                if (cameraInfo.name.isEmpty()) {
                    wchar_t driverDesc[256];
                    DWORD driverDescSize = sizeof(driverDesc);
                    if (RegQueryValueEx(hSubKey, L"DriverDesc", nullptr, nullptr,
                                        (LPBYTE)driverDesc, &driverDescSize) == ERROR_SUCCESS) {
                        cameraInfo.name = QString::fromWCharArray(driverDesc);
                    }
                }

                if (!cameraInfo.name.isEmpty()) {
                    QVector<QPair<int, int>> commonResolutions = {
                        {1920, 1080}, {1280, 720}, {1024, 768}, {800, 600}, {640, 480}, {320, 240}
                    };

                    for (const auto& res : commonResolutions) {
                        cameraInfo.capabilities.append(qMakePair(
                            QString("Разрешение"),
                            QString("%1x%2").arg(res.first).arg(res.second)
                            ));
                    }

                    cameraInfo.capabilities.append(qMakePair(QString("Тип"), QString("USB Camera")));
                    cameraInfo.capabilities.append(qMakePair(QString("Формат"), QString("MJPEG/YUY2")));
                    cameraInfo.capabilities.append(qMakePair(QString("FPS"), QString("30")));

                    cameras.append(cameraInfo);
                }

                RegCloseKey(hSubKey);
            }

            index++;
            keyNameSize = sizeof(keyName);
        }
        RegCloseKey(hKey);
    }

    if (cameras.isEmpty()) {
        cameras = getDemoCameraData();
    }

    return cameras;
}


QString Lab4Window::getDefaultCameraInfo()
{

    QString info;
    info += "===  ===\n";
    return info;
}

void Lab4Window::centerWindow()
{
    if (isMinimized() || isMaximized() || m_isSecretMode) {
        return;
    }

    QScreen *screen = QGuiApplication::primaryScreen();
    if (!screen) return;

    QRect screenGeometry = screen->availableGeometry();

    int x = (screenGeometry.width() - width()) / 2;
    int y = (screenGeometry.height() - height()) / 2;

    x = qMax(0, x);
    y = qMax(0, y);
    x = qMin(screenGeometry.width() - width(), x);
    y = qMin(screenGeometry.height() - height(), y);

    move(x, y);
}

void Lab4Window::initializeUI()
{
    setStyleSheet("QMainWindow { background-color: #F5F5DC; }");

    m_trayIcon = new QSystemTrayIcon(this);
    m_trayIcon->setIcon(QIcon(":/resources/images/m2.png"));
    m_trayIcon->setToolTip("Camera Application");
    m_trayIcon->hide();

    m_characterAnimation = new CharacterAnimation(this);
    m_characterAnimation->setFixedSize(120, 120);
    m_characterAnimation->setBackgroundColor(Qt::transparent);
    m_characterAnimation->hide();

    m_cameraCheckTimer = new QTimer(this);
    m_cameraCheckTimer->setInterval(1000);
}

void Lab4Window::setupCameraAnimation()
{
    m_cameraAnimation = new CharacterAnimation(this);
    m_cameraAnimation->setFixedSize(200, 200);
    m_cameraAnimation->setBackgroundColor(QColor(255, 255, 255, 100));

    QStringList spritePaths = {
        "C:/Users/atyme/OneDrive/Документы/db/AnimationLab/resources/images/lab4.png"
    };

    bool spriteLoaded = false;

    for (const QString& path : spritePaths) {
        QFile file(path);
        if (!file.exists()) {
            continue;
        }

        int frameWidth = 1130;
        int frameHeight = 1130;

        if (m_cameraAnimation->loadSpriteSheet(path, frameWidth, frameHeight)) {
            int loadedFrames = m_cameraAnimation->totalFrames();

            if (loadedFrames > 0) {
                spriteLoaded = true;
                m_cameraAnimation->setScaleFactor(0.18);
                m_cameraAnimation->setAnimationSpeed(150);
                break;
            }
        }
    }

    if (!spriteLoaded) {
        logMessage("Не удалось загрузить анимацию камеры");
        return;
    }

    updateCameraAnimationPosition();
}

void Lab4Window::setupConnections()
{
    connect(ui->btnTakePhoto, &QPushButton::clicked, this, &Lab4Window::onTakePhotoClicked);
    connect(ui->btnRecordVideo, &QPushButton::clicked, this, &Lab4Window::onRecordVideoClicked);
    connect(ui->btnCameraInfo, &QPushButton::clicked, this, &Lab4Window::onCameraInfoClicked);
    connect(ui->btnToggleSecret, &QPushButton::clicked, this, &Lab4Window::onToggleSecretClicked);
    connect(ui->btnBack, &QPushButton::clicked, this, &Lab4Window::onBackClicked);
    connect(m_trayIcon, &QSystemTrayIcon::activated, this, &Lab4Window::trayIconActivated);
    connect(m_cameraCheckTimer, &QTimer::timeout, this, &Lab4Window::checkCameraStatus);
}

void Lab4Window::applyStyles()
{
    QString buttonStyle =
        "QPushButton {"
        "padding: 8px 15px; font-size: 14px; font-weight: bold;"
        "background-color: #D2B48C; color: #8B4513; border-radius: 5px;"
        "border: 2px solid #A0522D;"
        "}"
        "QPushButton:hover { background-color: #BC8F8F; }"
        "QPushButton:pressed { background-color: #A0522D; color: white; }";

    ui->btnTakePhoto->setStyleSheet(buttonStyle);
    ui->btnRecordVideo->setStyleSheet(buttonStyle);
    ui->btnCameraInfo->setStyleSheet(buttonStyle);
    ui->btnToggleSecret->setStyleSheet(buttonStyle);
    ui->btnBack->setStyleSheet(buttonStyle);

    ui->groupBoxControls->setStyleSheet("QGroupBox { font-weight: bold; color: #8B4513; }");
    ui->groupBoxLog->setStyleSheet("QGroupBox { font-weight: bold; color: #8B4513; }");

    ui->textLog->setStyleSheet(
        "QTextEdit {"
        "background-color: white; border: 2px solid #A0522D; border-radius: 5px;"
        "font-family: 'Courier New'; font-size: 12px; padding: 10px;"
        "}");
}

void Lab4Window::setupAnimation()
{
    QStringList spritePaths = {
        "C:/Users/atyme/OneDrive/Документы/db/AnimationLab/resources/images/lab4.png",
        ":/resources/images/lab4.png",
        "resources/images/lab4.png"
    };

    bool spriteLoaded = false;
    for (const QString& path : spritePaths) {
        if (m_characterAnimation->loadSpriteSheet(path, 100, 100)) {
            spriteLoaded = true;
            break;
        }
    }

    if (!spriteLoaded) {
        logMessage("Ошибка загрузки спрайта для угловой анимации");
    }

    m_characterAnimation->setAnimationSpeed(100);
    updateAnimationPosition();
    m_cameraCheckTimer->start();
}

void Lab4Window::updateAnimationPosition()
{
    if (m_characterAnimation) {
        int x = width() - 120 - 20;
        int y = height() - 120 - 20;
        m_characterAnimation->move(x, y);
        m_characterAnimation->raise();
    }
}

void Lab4Window::updateCameraAnimationPosition()
{
    if (m_cameraAnimation) {
        int x = 550;
        int y = height() - 230;
        m_cameraAnimation->move(x, y);
        m_cameraAnimation->raise();
    }
}

void Lab4Window::showCameraAnimation(bool show)
{
    if (m_cameraAnimation) {
        if (show) {
            m_cameraAnimation->show();
            m_cameraAnimation->startAnimation();
            m_cameraAnimation->raise();
            logMessage("Анимация камеры включена");
        } else {
            m_cameraAnimation->hide();
            m_cameraAnimation->stopAnimation();
            logMessage("Анимация камеры выключена");
        }
    }
}

void Lab4Window::startCameraAnimation()
{
    if (!m_cameraActive && m_characterAnimation) {
        m_cameraActive = true;
        m_characterAnimation->show();
        m_characterAnimation->startAnimation();
        logMessage("ВНИМАНИЕ: Обнаружена активная камера!");
        updateAnimationPosition();
    }
}

void Lab4Window::stopCameraAnimation()
{
    if (m_cameraActive && m_characterAnimation) {
        m_cameraActive = false;
        m_characterAnimation->stopAnimation();
        m_characterAnimation->hide();
        logMessage("Камера отключена");
    }
}

bool Lab4Window::isCameraInUse()
{
    return m_isRecording;
}

void Lab4Window::checkCameraStatus()
{
    bool cameraInUse = isCameraInUse();

    if (cameraInUse && !m_cameraActive) {
        startCameraAnimation();
        showCameraAnimation(true);
    } else if (!cameraInUse && m_cameraActive) {
        stopCameraAnimation();
        showCameraAnimation(false);
    }
}

void Lab4Window::onTakePhotoClicked()
{
    logMessage("Начало создания фото...");

    showCameraAnimation(true);
    capturePhoto();

    QTimer::singleShot(2000, this, [this]() {
        if (!m_isRecording) {
            showCameraAnimation(false);
        }
    });
}

void Lab4Window::onRecordVideoClicked()
{
    if (m_isRecording) {
        logMessage("Остановка записи видео");
        stopVideoRecording();
    } else {
        int duration = ui->spinVideoDuration->value();
        logMessage(QString("Начало записи видео на %1 секунд").arg(duration));

        QString filename = generateFilename("video", "mp4");
        std::thread([this, duration, filename]() {
            recordVideo(duration, filename);
        }).detach();
    }
}

void Lab4Window::onCameraInfoClicked()
{
    logMessage("Получение информации о камерах...");
    printCameraInfo();
}

void Lab4Window::onToggleSecretClicked()
{
    toggleSecretMode(!m_isSecretMode);
}

void Lab4Window::onBackClicked()
{
    if (m_isRecording) {
        stopVideoRecording();
    }
    stopCameraAnimation();
    showCameraAnimation(false);
    m_cameraCheckTimer->stop();
    emit backToMain();
    close();
}

bool Lab4Window::initializeCamera(cv::VideoCapture &camera)
{
    if (!camera.open(DEFAULT_CAMERA_ID)) {
        logMessage("Ошибка открытия камеры");
        return false;
    }

    int width = static_cast<int>(camera.get(CAP_PROP_FRAME_WIDTH));
    int height = static_cast<int>(camera.get(CAP_PROP_FRAME_HEIGHT));
    double fps = camera.get(CAP_PROP_FPS);

    if (width <= 0 || height <= 0) {
        camera.set(CAP_PROP_FRAME_WIDTH, DEFAULT_WIDTH);
        camera.set(CAP_PROP_FRAME_HEIGHT, DEFAULT_HEIGHT);
        width = DEFAULT_WIDTH;
        height = DEFAULT_HEIGHT;
    }

    if (fps <= 0.1) {
        camera.set(CAP_PROP_FPS, DEFAULT_FPS);
        fps = DEFAULT_FPS;
    }

    logMessage(QString("Камера инициализирована: %1x%2, FPS: %3").arg(width).arg(height).arg(fps));
    return true;
}

bool Lab4Window::initializeVideoWriter(cv::VideoWriter &writer, const cv::VideoCapture &camera, const QString &filename)
{
    int width = static_cast<int>(camera.get(CAP_PROP_FRAME_WIDTH));
    int height = static_cast<int>(camera.get(CAP_PROP_FRAME_HEIGHT));
    double fps = camera.get(CAP_PROP_FPS);

    if (fps <= 0.1) {
        fps = DEFAULT_FPS;
    }

    int fourcc = VideoWriter::fourcc('m', 'p', '4', 'v');
    bool success = writer.open(filename.toStdString(), fourcc, fps, Size(width, height), true);

    if (!success) {
        QString aviFilename = filename;
        aviFilename.replace(".mp4", ".avi");
        fourcc = VideoWriter::fourcc('M', 'J', 'P', 'G');
        success = writer.open(aviFilename.toStdString(), fourcc, fps, Size(width, height), true);

        if (!success) {
            fourcc = VideoWriter::fourcc('X', 'V', 'I', 'D');
            success = writer.open(aviFilename.toStdString(), fourcc, fps, Size(width, height), true);
        }
    }

    return success;
}

void Lab4Window::capturePhoto()
{
    try {
        Mat frame;
        VideoCapture cap;

        if (!initializeCamera(cap)) {
            return;
        }

        if (cap.read(frame) && !frame.empty()) {
            QString filename = generateFilename("photo", "jpg");
            vector<int> compression_params = {IMWRITE_JPEG_QUALITY, 95};

            imwrite(filename.toStdString(), frame, compression_params);
            logMessage("Фото сохранено: " + filename);
        } else {
            logMessage("Ошибка захвата кадра");
        }

    } catch (const std::exception& e) {
        logMessage(QString("Ошибка создания фото: %1").arg(e.what()));
    }
}

void Lab4Window::recordVideo(int seconds, const QString &filename)
{
    try {
        showCameraAnimation(true);

        VideoCapture cap;
        if (!initializeCamera(cap)) {
            showCameraAnimation(false);
            return;
        }

        int width = static_cast<int>(cap.get(CAP_PROP_FRAME_WIDTH));
        int height = static_cast<int>(cap.get(CAP_PROP_FRAME_HEIGHT));
        double fps = cap.get(CAP_PROP_FPS);

        if (fps <= 0.1) {
            fps = DEFAULT_FPS;
        }

        logMessage(QString("Параметры записи: %1x%2, FPS: %3, длительность: %4 сек")
                       .arg(width).arg(height).arg(fps).arg(seconds));

        VideoWriter writer;
        if (!initializeVideoWriter(writer, cap, filename)) {
            logMessage("Ошибка создания видеофайла");
            showCameraAnimation(false);
            return;
        }

        m_isRecording = true;
        Mat frame;
        auto startTime = chrono::steady_clock::now();
        auto targetDuration = chrono::seconds(seconds);

        logMessage("Начало записи видео...");

        while (m_isRecording) {
            auto currentTime = chrono::steady_clock::now();
            auto elapsedTime = chrono::duration_cast<chrono::seconds>(currentTime - startTime);

            if (elapsedTime >= targetDuration) {
                break;
            }

            if (!cap.read(frame) || frame.empty()) {
                logMessage("Ошибка чтения кадра");
                break;
            }

            writer.write(frame);

            this_thread::sleep_for(chrono::milliseconds(10));
        }

        auto endTime = chrono::steady_clock::now();
        auto totalDuration = chrono::duration_cast<chrono::seconds>(endTime - startTime).count();

        logMessage(QString("Видео успешно сохранено: %1 (длительность: %2 сек)").arg(filename).arg(totalDuration));

        m_isRecording = false;
        showCameraAnimation(false);

    } catch (const std::exception& e) {
        logMessage(QString("Ошибка при захвате видео: %1").arg(e.what()));
        m_isRecording = false;
        showCameraAnimation(false);
    }
}

void Lab4Window::startVideoRecording()
{
    if (m_isRecording) {
        logMessage("Запись уже идет");
        return;
    }

    try {
        m_videoCapture = new VideoCapture();
        if (!initializeCamera(*m_videoCapture)) {
            delete m_videoCapture;
            m_videoCapture = nullptr;
            return;
        }

        int width = static_cast<int>(m_videoCapture->get(CAP_PROP_FRAME_WIDTH));
        int height = static_cast<int>(m_videoCapture->get(CAP_PROP_FRAME_HEIGHT));
        double fps = m_videoCapture->get(CAP_PROP_FPS);

        logMessage(QString("Параметры непрерывной записи: %1x%2, FPS: %3").arg(width).arg(height).arg(fps));

        QString outputFile = generateFilename("continuous_video", "mp4");
        m_videoWriter = new VideoWriter();

        if (!initializeVideoWriter(*m_videoWriter, *m_videoCapture, outputFile)) {
            logMessage("Ошибка создания видеофайла");
            delete m_videoCapture;
            m_videoCapture = nullptr;
            delete m_videoWriter;
            m_videoWriter = nullptr;
            return;
        }

        m_isRecording = true;
        m_stopRecordingRequested = false;
        m_recordThread = new std::thread(&Lab4Window::videoRecordingThread, this);
        logMessage("Начата непрерывная запись видео: " + outputFile);

    } catch (const std::exception& e) {
        logMessage(QString("Ошибка при запуске записи: %1").arg(e.what()));
    }
}

void Lab4Window::stopVideoRecording()
{
    if (!m_isRecording) {
        return;
    }

    logMessage("Запрос остановки записи...");
    m_stopRecordingRequested = true;

    if (m_recordThread && m_recordThread->joinable()) {
        m_recordThread->join();
        delete m_recordThread;
        m_recordThread = nullptr;
    }

    if (m_videoWriter) {
        m_videoWriter->release();
        delete m_videoWriter;
        m_videoWriter = nullptr;
    }

    if (m_videoCapture) {
        m_videoCapture->release();
        delete m_videoCapture;
        m_videoCapture = nullptr;
    }

    m_isRecording = false;
    logMessage("Запись видео завершена");
}

void Lab4Window::videoRecordingThread()
{
    try {
        Mat frame;
        int frameCount = 0;
        auto startTime = chrono::steady_clock::now();

        while (m_isRecording && !m_stopRecordingRequested) {
            if (!m_videoCapture->read(frame) || frame.empty()) {
                logMessage("Ошибка чтения кадра из камеры");
                break;
            }

            m_videoWriter->write(frame);
            frameCount++;
            this_thread::sleep_for(chrono::milliseconds(1));
        }

        auto endTime = chrono::steady_clock::now();
        auto totalDuration = chrono::duration_cast<chrono::seconds>(endTime - startTime).count();

        logMessage(QString("Запись завершена: %1 кадров, %2 секунд").arg(frameCount).arg(totalDuration));
        m_isRecording = false;

    } catch (const std::exception& e) {
        logMessage(QString("Ошибка в потоке записи видео: %1").arg(e.what()));
        m_isRecording = false;
    }
}

void Lab4Window::printCameraInfo()
{
    logMessage("=== ИНФОРМАЦИЯ О КАМЕРАХ ===");

    try {
        QVector<CameraInfo> cameras = getCameraInfoLowLevel();

        if (cameras.isEmpty()) {
            logMessage("Камеры не обнаружены в системе");
        } else {
            logMessage(QString("Найдено камер: %1").arg(cameras.size()));

            for (int i = 0; i < cameras.size(); ++i) {
                const CameraInfo& camera = cameras[i];
                logMessage(QString("\n--- Камера %1 ---").arg(i + 1));
                logMessage(QString("Название: %1").arg(camera.name));
                if (!camera.description.isEmpty()) {
                    logMessage(QString("Описание: %1").arg(camera.description));
                }
                if (!camera.devicePath.isEmpty()) {
                    logMessage(QString("Путь: %1").arg(camera.devicePath));
                }

                if (!camera.capabilities.isEmpty()) {
                    logMessage("Возможности:");
                    for (const auto& capability : camera.capabilities) {
                        logMessage(QString("  %1: %2").arg(capability.first).arg(capability.second));
                    }
                }
            }
        }

        logMessage("\n" + getDefaultCameraInfo());
        logMessage("=== КОНЕЦ ИНФОРМАЦИИ ===");

    } catch (const std::exception& e) {
        logMessage(QString("Ошибка получения информации: %1").arg(e.what()));
    }
}

void Lab4Window::toggleSecretMode(bool enable)
{
    if (enable) {
        m_savedPosition = pos();
        m_savedSize = size();
        m_isMaximized = isMaximized();

        m_isSecretMode = true;
        ui->btnToggleSecret->setText("Выйти из скрытого режима");

        hide();
        m_trayIcon->show();
        logMessage("Включен скрытый режим");
    } else {
        if (m_isRecording) {
            stopVideoRecording();
        }
        m_isSecretMode = false;
        ui->btnToggleSecret->setText("Войти в скрытый режим");

        show();

        if (m_isMaximized) {
            showMaximized();
        } else {
            if (!m_savedPosition.isNull() && m_savedSize.isValid()) {
                setGeometry(m_savedPosition.x(), m_savedPosition.y(),
                            m_savedSize.width(), m_savedSize.height());
            }

            QTimer::singleShot(50, this, &Lab4Window::centerWindow);
        }

        raise();
        activateWindow();
        setFocus();

        m_trayIcon->hide();
        logMessage("Выход из скрытого режима");
    }
}

void Lab4Window::registerHotkey()
{
    if (!RegisterHotKey((HWND)winId(), HOTKEY_SHOW, MOD_CONTROL | MOD_ALT, 'A')) {
        logMessage("Ошибка регистрации горячей клавиши Ctrl+Alt+A");
    }

    if (!RegisterHotKey((HWND)winId(), HOTKEY_PHOTO, MOD_CONTROL | MOD_ALT, 'S')) {
        logMessage("Ошибка регистрации горячей клавиши Ctrl+Alt+S");
    }

    if (!RegisterHotKey((HWND)winId(), HOTKEY_VIDEO, MOD_CONTROL | MOD_ALT, 'D')) {
        logMessage("Ошибка регистрации горячей клавиши Ctrl+Alt+D");
    }
}

void Lab4Window::unregisterHotkey()
{
    UnregisterHotKey((HWND)winId(), HOTKEY_SHOW);
    UnregisterHotKey((HWND)winId(), HOTKEY_PHOTO);
    UnregisterHotKey((HWND)winId(), HOTKEY_VIDEO);
}

bool Lab4Window::nativeEvent(const QByteArray &eventType, void *message, long long *result)
{
    MSG *msg = static_cast<MSG*>(message);
    if (msg->message == WM_HOTKEY) {
        switch (msg->wParam) {
        case HOTKEY_SHOW:
            toggleSecretMode(!m_isSecretMode);
            return true;
        case HOTKEY_PHOTO:
            if (m_isSecretMode) {
                logMessage("Захват фото по горячей клавише");
                capturePhoto();
            }
            return true;
        case HOTKEY_VIDEO:
            if (m_isSecretMode) {
                if (m_isRecording) {
                    logMessage("Остановка записи видео по горячей клавише");
                    stopVideoRecording();
                } else {
                    logMessage("Начало записи видео по горячей клавише");
                    startVideoRecording();
                }
            }
            return true;
        }
    }
    return QMainWindow::nativeEvent(eventType, message, result);
}

void Lab4Window::trayIconActivated(QSystemTrayIcon::ActivationReason reason)
{
    if (reason == QSystemTrayIcon::DoubleClick) {
        toggleSecretMode(false);
    }
}

void Lab4Window::logMessage(const QString &message)
{
    QString timestamp = generateTimestamp();
    ui->textLog->append(QString("[%1] %2").arg(timestamp, message));

    QScrollBar *scrollBar = ui->textLog->verticalScrollBar();
    scrollBar->setValue(scrollBar->maximum());
}

QString Lab4Window::generateTimestamp() const
{
    return QDateTime::currentDateTime().toString("hh:mm:ss");
}

QString Lab4Window::generateFilename(const QString &prefix, const QString &extension) const
{
    return QString("%1_%2.%3")
    .arg(prefix)
        .arg(QDateTime::currentDateTime().toString("yyyyMMdd_hhmmss_zzz"))
        .arg(extension);
}

QVector<CameraInfo> Lab4Window::getDemoCameraData()
{
    QVector<CameraInfo> cameras;

    CameraInfo mainCamera;
    mainCamera.name = "Integrated Camera";
    mainCamera.description = "USB Video Device";
    mainCamera.devicePath = "USB\\VID_13D3&PID_56FB&MI_00\\7&3129022C&1&0000";

    QVector<QPair<int, int>> mainResolutions = {
        {1920, 1080}, {1280, 720}, {1024, 768}, {800, 600}, {640, 480}
    };

    for (const auto& res : mainResolutions) {
        mainCamera.capabilities.append(qMakePair(
            QString("Разрешение"),
            QString("%1x%2").arg(res.first).arg(res.second)
            ));
    }

    mainCamera.capabilities.append(qMakePair(QString("Тип"), QString("USB Camera")));
    mainCamera.capabilities.append(qMakePair(QString("Формат"), QString("MJPEG")));
    mainCamera.capabilities.append(qMakePair(QString("FPS"), QString("30")));
    mainCamera.capabilities.append(qMakePair(QString("Производитель"), QString("VID_13D3")));
    mainCamera.capabilities.append(qMakePair(QString("Модель"), QString("PID_56FB")));

    cameras.append(mainCamera);

    CameraInfo irCamera;
    irCamera.name = "Integrated IR Camera";
    irCamera.description = "Realtek DMFT - IR";
    irCamera.devicePath = "USB\\VID_13D3&PID_56FB&MI_02\\7&3129022C&1&0002";

    QVector<QPair<int, int>> irResolutions = {
        {1280, 720}, {640, 480}, {320, 240}
    };

    for (const auto& res : irResolutions) {
        irCamera.capabilities.append(qMakePair(
            QString("Разрешение"),
            QString("%1x%2").arg(res.first).arg(res.second)
            ));
    }

    irCamera.capabilities.append(qMakePair(QString("Тип"), QString("IR Camera")));
    irCamera.capabilities.append(qMakePair(QString("Назначение"), QString("Windows Hello Face Recognition")));
    irCamera.capabilities.append(qMakePair(QString("Формат"), QString("YUY2")));
    irCamera.capabilities.append(qMakePair(QString("FPS"), QString("15")));
    irCamera.capabilities.append(qMakePair(QString("Производитель"), QString("Realtek")));

    cameras.append(irCamera);

    CameraInfo dfuCamera;
    dfuCamera.name = "Camera DFU Device";
    dfuCamera.description = "Устройство WinUSB";
    dfuCamera.devicePath = "USB\\VID_13D3&PID_56FB&MI_04\\7&3129022C&1&0004";

    dfuCamera.capabilities.append(qMakePair(QString("Тип"), QString("DFU (Device Firmware Update)")));
    dfuCamera.capabilities.append(qMakePair(QString("Назначение"), QString("Обновление прошивки камеры")));
    dfuCamera.capabilities.append(qMakePair(QString("Интерфейс"), QString("WinUSB")));
    dfuCamera.capabilities.append(qMakePair(QString("Производитель"), QString("VID_13D3")));

    cameras.append(dfuCamera);

    return cameras;
}


void Lab4Window::closeEvent(QCloseEvent *event)
{
    if (m_isSecretMode) {
        hide();
        event->ignore();
    } else {
        if (m_trayIcon) {
            m_trayIcon->hide();
        }
        stopCameraAnimation();
        showCameraAnimation(false);
        m_cameraCheckTimer->stop();
        QMainWindow::closeEvent(event);
    }
}

void Lab4Window::resizeEvent(QResizeEvent *event)
{
    QMainWindow::resizeEvent(event);
    updateAnimationPosition();
    updateCameraAnimationPosition();
}

void Lab4Window::showEvent(QShowEvent *event)
{
    QMainWindow::showEvent(event);

    if (!m_isSecretMode) {
        QTimer::singleShot(100, this, &Lab4Window::centerWindow);
    }

    updateAnimationPosition();
    updateCameraAnimationPosition();
}
