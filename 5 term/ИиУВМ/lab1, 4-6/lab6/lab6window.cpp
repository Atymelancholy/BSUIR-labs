#include "lab6window.h"
#include "characteranimation.h"

#include <QFileDialog>
#include <QMessageBox>
#include <QScrollBar>
#include <QScreen>
#include <QGuiApplication>
#include <QCloseEvent>
#include <QShowEvent>
#include <QResizeEvent>
#include <QDateTime>
#include <QFileInfo>
#include <QDir>
#include <QProcess>
#include <QDesktopServices>
#include <QUrl>
#include <QDebug>
#include <QFile>
#include <QMimeDatabase>
#include <QApplication>

#include <iostream>
#include <fstream>
#include <vector>
#include <sstream>
#include <thread>
#include <chrono>

using namespace std;

extern "C" {
int connect(SOCKET s, const struct sockaddr *name, int namelen);
int bind(SOCKET s, const struct sockaddr *addr, int addrlen);
int listen(SOCKET s, int backlog);
SOCKET accept(SOCKET s, struct sockaddr *addr, int *addrlen);
int send(SOCKET s, const char *buf, int len, int flags);
int recv(SOCKET s, char *buf, int len, int flags);
int closesocket(SOCKET s);
int getsockname(SOCKET s, struct sockaddr *name, int *namelen);
}

Lab6Window::Lab6Window(QWidget *parent) :
    QMainWindow(parent),
    m_centralWidget(nullptr),
    m_devicesGroup(nullptr),
    m_transferGroup(nullptr),
    m_logGroup(nullptr),
    m_devicesList(nullptr),
    m_scanButton(nullptr),
    m_sendButton(nullptr),
    m_receiveButton(nullptr),
    m_backButton(nullptr),
    m_logText(nullptr),
    m_progressBar(nullptr),
    m_statusLabel(nullptr),
    m_characterAnimation(nullptr),
    m_trayIcon(nullptr),
    m_statusTimer(nullptr),
    m_isScanning(false),
    m_isTransferring(false),
    m_isReceiving(false),
    m_scanThread(nullptr),
    m_transferThread(nullptr),
    m_serverThread(nullptr),
    m_serverSocket(INVALID_SOCKET),
    m_clientSocket(INVALID_SOCKET),
    m_selectedDeviceAddr(0)
{
    setWindowTitle("Лабораторная работа 6 - Bluetooth File Transfer");
    resize(1000, 800);

    WSADATA wsaData;
    if (WSAStartup(MAKEWORD(2, 2), &wsaData) != 0) {
        qDebug() << "Ошибка инициализации Winsock";
    }

    initializeUI();
    setupConnections();
    applyStyles();
    initializeCharacterAnimation();

    m_statusTimer = new QTimer(this);
    connect(m_statusTimer, &QTimer::timeout, this, &Lab6Window::updateBluetoothStatus);
    m_statusTimer->start(3000);

    QTimer::singleShot(100, this, &Lab6Window::centerWindow);

    logMessage("=== Bluetooth File Transfer инициализирован ===");
    logMessage("Режим: РЕАЛЬНЫЕ Bluetooth устройства");
    updateBluetoothStatus();
}

Lab6Window::~Lab6Window()
{
    stopBluetoothServer();

    if (m_scanThread && m_scanThread->joinable()) {
        m_isScanning = false;
        m_scanThread->join();
        delete m_scanThread;
    }

    if (m_transferThread && m_transferThread->joinable()) {
        m_isTransferring = false;
        m_transferThread->join();
        delete m_transferThread;
    }

    if (m_serverThread && m_serverThread->joinable()) {
        m_isReceiving = false;
        m_serverThread->join();
        delete m_serverThread;
    }

    if (m_serverSocket != INVALID_SOCKET) {
        closesocket(m_serverSocket);
    }
    if (m_clientSocket != INVALID_SOCKET) {
        closesocket(m_clientSocket);
    }

    WSACleanup();

    delete m_characterAnimation;
}

void Lab6Window::initializeUI()
{
    setStyleSheet("QMainWindow { background-color: #F5F5DC; }");

    m_centralWidget = new QWidget(this);
    setCentralWidget(m_centralWidget);

    QVBoxLayout *mainLayout = new QVBoxLayout(m_centralWidget);
    mainLayout->setContentsMargins(20, 20, 20, 20);
    mainLayout->setSpacing(20);

    QLabel *titleLabel = new QLabel("Bluetooth File Transfer - Реальная передача файлов", m_centralWidget);
    titleLabel->setStyleSheet("font-size: 20px; font-weight: bold; color: #8B4513; text-align: center;");
    titleLabel->setAlignment(Qt::AlignCenter);

    QHBoxLayout *topLayout = new QHBoxLayout();
    topLayout->setSpacing(30);

    m_devicesGroup = new QGroupBox("Bluetooth Устройства в сети", m_centralWidget);
    m_devicesGroup->setMinimumWidth(500);
    QVBoxLayout *devicesLayout = new QVBoxLayout(m_devicesGroup);

    m_devicesList = new QListWidget(m_devicesGroup);
    m_devicesList->setMinimumHeight(300);

    m_scanButton = new QPushButton("🔍 Сканировать REAL устройства", m_devicesGroup);
    m_scanButton->setMinimumHeight(40);

    devicesLayout->addWidget(m_devicesList);
    devicesLayout->addWidget(m_scanButton);

    m_transferGroup = new QGroupBox("Управление передачей", m_centralWidget);
    m_transferGroup->setMinimumWidth(400);
    QVBoxLayout *transferLayout = new QVBoxLayout(m_transferGroup);

    m_sendButton = new QPushButton("📤 Отправить файл", m_transferGroup);
    m_sendButton->setMinimumHeight(40);

    m_receiveButton = new QPushButton("📥 Запустить сервер приема", m_transferGroup);
    m_receiveButton->setMinimumHeight(40);

    m_progressBar = new QProgressBar(m_transferGroup);
    m_progressBar->setValue(0);
    m_progressBar->setMinimum(0);
    m_progressBar->setMaximum(100);
    m_progressBar->setMinimumHeight(25);

    m_statusLabel = new QLabel("Статус: Проверка Bluetooth...", m_transferGroup);
    m_statusLabel->setAlignment(Qt::AlignCenter);
    m_statusLabel->setMinimumHeight(30);

    QLabel *infoLabel = new QLabel(
        "Инструкция:\n"
        "1. Запустите сервер на принимающем ноутбуке\n"
        "2. Отсканируйте устройства на отправляющем\n"
        "3. Выберите устройство и отправьте файл\n"
        "4. Файл автоматически воспроизведется после получения\n"
        "5. Приложение НЕ закрывается после передачи - можно отправлять еще файлы!", m_transferGroup);
    infoLabel->setStyleSheet("font-size: 11px; color: #654321; background-color: rgba(210,180,140,0.3); padding: 10px; border-radius: 5px;");
    infoLabel->setWordWrap(true);

    transferLayout->addWidget(m_sendButton);
    transferLayout->addWidget(m_receiveButton);
    transferLayout->addWidget(m_progressBar);
    transferLayout->addWidget(m_statusLabel);
    transferLayout->addWidget(infoLabel);
    transferLayout->addStretch();

    topLayout->addWidget(m_devicesGroup);
    topLayout->addWidget(m_transferGroup);

    m_logGroup = new QGroupBox("Лог операций", m_centralWidget);
    QVBoxLayout *logLayout = new QVBoxLayout(m_logGroup);

    m_logText = new QTextEdit(m_logGroup);
    m_logText->setMaximumHeight(200);
    m_logText->setReadOnly(true);

    logLayout->addWidget(m_logText);

    m_backButton = new QPushButton("← В главное меню", m_centralWidget);
    m_backButton->setMinimumHeight(35);

    mainLayout->addWidget(titleLabel);
    mainLayout->addLayout(topLayout);
    mainLayout->addWidget(m_logGroup);
    mainLayout->addWidget(m_backButton);

    m_trayIcon = new QSystemTrayIcon(this);
    m_trayIcon->setIcon(QIcon(":/resources/images/bluetooth.png"));
    m_trayIcon->setToolTip("Bluetooth File Transfer");
    m_trayIcon->hide();
}

void Lab6Window::setupConnections()
{
    connect(m_scanButton, &QPushButton::clicked, this, &Lab6Window::onScanDevicesClicked);
    connect(m_sendButton, &QPushButton::clicked, this, &Lab6Window::onSendFileClicked);
    connect(m_receiveButton, &QPushButton::clicked, this, &Lab6Window::onReceiveFileClicked);
    connect(m_backButton, &QPushButton::clicked, this, &Lab6Window::onBackClicked);
    connect(m_devicesList, &QListWidget::itemClicked, this, &Lab6Window::onDeviceSelected);
}

void Lab6Window::applyStyles()
{
    QString buttonStyle =
        "QPushButton {"
        "padding: 12px 20px; font-size: 14px; font-weight: bold;"
        "background-color: #D2B48C; color: #8B4513; border-radius: 8px;"
        "border: 2px solid #A0522D; min-height: 20px;"
        "}"
        "QPushButton:hover { background-color: #BC8F8F; }"
        "QPushButton:pressed { background-color: #A0522D; color: white; }"
        "QPushButton:disabled { background-color: #E8E8E8; color: #A0A0A0; }";

    m_scanButton->setStyleSheet(buttonStyle);
    m_sendButton->setStyleSheet(buttonStyle);
    m_receiveButton->setStyleSheet(buttonStyle);
    m_backButton->setStyleSheet(buttonStyle);

    m_devicesGroup->setStyleSheet("QGroupBox { font-weight: bold; color: #8B4513; font-size: 14px; }");
    m_transferGroup->setStyleSheet("QGroupBox { font-weight: bold; color: #8B4513; font-size: 14px; }");
    m_logGroup->setStyleSheet("QGroupBox { font-weight: bold; color: #8B4513; font-size: 14px; }");

    m_logText->setStyleSheet(
        "QTextEdit {"
        "background-color: white; border: 2px solid #A0522D; border-radius: 8px;"
        "font-family: 'Consolas'; font-size: 11px; padding: 12px;"
        "selection-background-color: #D2B48C;"
        "}");

    m_progressBar->setStyleSheet(
        "QProgressBar {"
        "border: 2px solid #A0522D; border-radius: 6px; text-align: center;"
        "background-color: #F5F5DC; font-weight: bold;"
        "}"
        "QProgressBar::chunk {"
        "background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, "
        "stop:0 #D2B48C, stop:1 #A0522D);"
        "border-radius: 4px;"
        "}");

    m_statusLabel->setStyleSheet(
        "QLabel {"
        "background-color: rgba(139, 69, 19, 0.1);"
        "border: 2px solid #A0522D; border-radius: 6px;"
        "padding: 8px; font-size: 12px; font-weight: bold;"
        "color: #8B4513;"
        "}");

    m_devicesList->setStyleSheet(
        "QListWidget {"
        "background-color: white; border: 2px solid #A0522D; border-radius: 8px;"
        "font-family: 'Segoe UI'; font-size: 12px; padding: 8px;"
        "alternate-background-color: #FAF0E6;"
        "}"
        "QListWidget::item {"
        "padding: 10px; border-bottom: 1px solid #D2B48C;"
        "border-radius: 4px; margin: 2px;"
        "}"
        "QListWidget::item:selected {"
        "background-color: #D2B48C; color: #8B4513; font-weight: bold;"
        "border: 1px solid #A0522D;"
        "}"
        "QListWidget::item:hover {"
        "background-color: #E8D0B3;"
        "}");
}

void Lab6Window::initializeCharacterAnimation()
{
    qDebug() << "Инициализация анимации Bluetooth...";

    m_characterAnimation = new CharacterAnimation(this);
    m_characterAnimation->setFixedSize(150, 150);
    m_characterAnimation->setBackgroundColor(Qt::transparent);

    QStringList spritePaths = {
        "C:/Users/atyme/OneDrive/Документы/db/AnimationLab/resources/images/l6.png",
        ":/resources/images/l6.png",
        "resources/images/l6.png",
        "C:/Users/atyme/OneDrive/Документы/db/AnimationLab/resources/images/lab6.png",
        ":/resources/images/lab6.png",
        "resources/images/lab6.png",
        "C:/Users/atyme/OneDrive/Документы/db/AnimationLab/resources/images/bluetooth_animation.png",
        ":/resources/images/bluetooth_animation.png",
        "C:/Users/atyme/OneDrive/Документы/db/AnimationLab/resources/images/bluetooth.png",
        ":/resources/images/bluetooth.png"
    };

    bool spriteLoaded = false;

    QList<QPair<int, int>> frameSizes = {
        {1920, 1080}
    };

    for (const QString& path : spritePaths) {
        for (const auto& frameSize : frameSizes) {
            int frameWidth = frameSize.first;
            int frameHeight = frameSize.second;

            qDebug() << "Попытка загрузки:" << path << "с размером кадра:" << frameWidth << "x" << frameHeight;

            if (m_characterAnimation->loadSpriteSheet(path, frameWidth, frameHeight)) {
                spriteLoaded = true;
                qDebug() << "УСПЕХ: Спрайт загружен! Размер кадра:" << frameWidth << "x" << frameHeight;

                m_characterAnimation->setScaleFactor(0.15);
                m_characterAnimation->setAnimationSpeed(150);
                m_characterAnimation->setFixedSize(250, 200);

                break;
            }
        }
        if (spriteLoaded) break;
    }

    if (!spriteLoaded) {
        qDebug() << "Не удалось загрузить анимацию Bluetooth. Создаем заглушку.";

        QWidget *debugWidget = new QWidget(this);
        debugWidget->setFixedSize(120, 120);
        debugWidget->setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #4A90E2, stop:1 #357ABD); border: 2px solid #2C5AA0; border-radius: 10px;");

        QLabel *debugLabel = new QLabel("BT\nTRANSFER", debugWidget);
        debugLabel->setAlignment(Qt::AlignCenter);
        debugLabel->setStyleSheet("color: white; font-size: 14px; font-weight: bold; background: transparent;");
        debugLabel->resize(120, 120);

        debugWidget->setVisible(false);
        m_characterAnimation = reinterpret_cast<CharacterAnimation*>(debugWidget);
    }

    updateAnimationPosition();
    m_characterAnimation->raise();
    m_characterAnimation->hide();

    qDebug() << "Анимация Bluetooth инициализирована. Размер:" << m_characterAnimation->size();
}

void Lab6Window::startConnectionAnimation()
{
    qDebug() << ">>> ЗАПУСК АНИМАЦИИ ПОДКЛЮЧЕНИЯ BLUETOOTH";

    if (m_characterAnimation) {
        m_characterAnimation->show();
        m_characterAnimation->raise();

        CharacterAnimation* animation = qobject_cast<CharacterAnimation*>(m_characterAnimation);
        if (animation) {
            qDebug() << "Запуск CharacterAnimation для подключения Bluetooth...";
            qDebug() << " - Размер:" << animation->size();
            qDebug() << " - Позиция:" << animation->pos();
            qDebug() << " - Видимость:" << animation->isVisible();

            animation->startAnimation();
            qDebug() << "Анимация подключения Bluetooth ЗАПУЩЕНА";

        } else {
            qDebug() << "Используется ЗАГЛУШКА анимации для подключения Bluetooth";
            QWidget* debugWidget = qobject_cast<QWidget*>(m_characterAnimation);
            if (debugWidget) {
                debugWidget->setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #4CAF50, stop:1 #45a049); border: 2px solid #2E7D32; border-radius: 10px;");
                QLabel* label = debugWidget->findChild<QLabel*>();
                if (label) {
                    label->setText("BT\n✓");
                    label->setStyleSheet("color: white; font-weight: bold; font-size: 14px; background: transparent;");
                }
                debugWidget->show();
            }
        }

        QTimer::singleShot(3000, this, [this]() {
            qDebug() << "<<< Скрытие анимации подключения Bluetooth";
            if (m_characterAnimation && m_characterAnimation->isVisible()) {
                CharacterAnimation* animation = qobject_cast<CharacterAnimation*>(m_characterAnimation);
                if (animation) {
                    animation->stopAnimation();
                }
                m_characterAnimation->hide();
            }
        });
    } else {
        qDebug() << "ОШИБКА: m_characterAnimation is null";
    }
}

void Lab6Window::startTransferAnimation()
{
    qDebug() << ">>> ЗАПУСК АНИМАЦИИ ПЕРЕДАЧИ BLUETOOTH";

    if (m_characterAnimation) {
        m_characterAnimation->show();
        m_characterAnimation->raise();

        CharacterAnimation* animation = qobject_cast<CharacterAnimation*>(m_characterAnimation);
        if (animation) {
            qDebug() << "Запуск CharacterAnimation для передачи Bluetooth...";
            animation->startAnimation();
            qDebug() << "Анимация передачи Bluetooth ЗАПУЩЕНА";
        } else {
            qDebug() << "Используется ЗАГЛУШКА анимации для передачи Bluetooth";
            QWidget* debugWidget = qobject_cast<QWidget*>(m_characterAnimation);
            if (debugWidget) {
                debugWidget->setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #2196F3, stop:1 #1976D2); border: 2px solid #0D47A1; border-radius: 10px;");
                QLabel* label = debugWidget->findChild<QLabel*>();
                if (label) {
                    label->setText("BT\n↻");
                    label->setStyleSheet("color: white; font-weight: bold; font-size: 14px; background: transparent;");
                }
                debugWidget->show();
            }
        }
    } else {
        qDebug() << "ОШИБКА: m_characterAnimation is null";
    }
}

void Lab6Window::stopTransferAnimation()
{
    qDebug() << "<<< ОСТАНОВКА АНИМАЦИИ ПЕРЕДАЧИ BLUETOOTH";
    if (m_characterAnimation && m_characterAnimation->isVisible()) {
        CharacterAnimation* animation = qobject_cast<CharacterAnimation*>(m_characterAnimation);
        if (animation) {
            animation->stopAnimation();
        }
        m_characterAnimation->hide();
    }
}

void Lab6Window::updateAnimationPosition()
{
    if (m_characterAnimation) {
        int x = width() - m_characterAnimation->width() - 20;
        int y = height() - m_characterAnimation->height() - 20;

        if (x < 0) x = 20;
        if (y < 0) y = 20;

        m_characterAnimation->move(x, y);
        m_characterAnimation->raise();

        qDebug() << "Анимация Bluetooth позиционирована: (" << x << "," << y
                 << "), размер:" << m_characterAnimation->size();
    }
}

void Lab6Window::centerWindow()
{
    QScreen *screen = QGuiApplication::primaryScreen();
    if (!screen) return;

    QRect screenGeometry = screen->availableGeometry();
    int x = (screenGeometry.width() - width()) / 2;
    int y = (screenGeometry.height() - height()) / 2;

    move(x, y);
}

bool Lab6Window::isBluetoothEnabled()
{
    BLUETOOTH_FIND_RADIO_PARAMS findParams = { sizeof(BLUETOOTH_FIND_RADIO_PARAMS) };
    HANDLE hRadio = nullptr;
    HBLUETOOTH_RADIO_FIND hFind = BluetoothFindFirstRadio(&findParams, &hRadio);

    bool enabled = (hFind != nullptr);

    if (hFind) {
        BluetoothFindRadioClose(hFind);
    }
    if (hRadio) {
        CloseHandle(hRadio);
    }

    return enabled;
}

QString Lab6Window::getBluetoothRadioInfo()
{
    BLUETOOTH_FIND_RADIO_PARAMS findParams = { sizeof(BLUETOOTH_FIND_RADIO_PARAMS) };
    HANDLE hRadio = nullptr;
    HBLUETOOTH_RADIO_FIND hFind = BluetoothFindFirstRadio(&findParams, &hRadio);

    if (!hFind) {
        return "❌ Bluetooth адаптер не найден или отключен";
    }

    BLUETOOTH_RADIO_INFO radioInfo = { sizeof(BLUETOOTH_RADIO_INFO) };
    DWORD result = BluetoothGetRadioInfo(hRadio, &radioInfo);

    QString info;
    if (result == ERROR_SUCCESS) {
        wstring deviceName(radioInfo.szName);
        QString address = QString::number(radioInfo.address.ullLong, 16).toUpper();
        info = QString("✅ Bluetooth адаптер: %1\n📡 MAC-адрес: %2")
                   .arg(QString::fromStdWString(deviceName))
                   .arg(address);
    } else {
        info = "⚠️ Не удалось получить информацию о Bluetooth адаптере";
    }

    BluetoothFindRadioClose(hFind);
    if (hRadio) {
        CloseHandle(hRadio);
    }

    return info;
}

QVector<BLUETOOTH_DEVICE_INFO> Lab6Window::enumerateBluetoothDevices()
{
    QVector<BLUETOOTH_DEVICE_INFO> devices;

    BLUETOOTH_DEVICE_SEARCH_PARAMS searchParams = { sizeof(BLUETOOTH_DEVICE_SEARCH_PARAMS) };
    searchParams.fReturnAuthenticated = TRUE;
    searchParams.fReturnConnected = TRUE;
    searchParams.fReturnRemembered = TRUE;
    searchParams.fReturnUnknown = TRUE;
    searchParams.cTimeoutMultiplier = 10;

    BLUETOOTH_DEVICE_INFO deviceInfo = { sizeof(BLUETOOTH_DEVICE_INFO), 0 };

    HBLUETOOTH_DEVICE_FIND hFind = BluetoothFindFirstDevice(&searchParams, &deviceInfo);
    if (hFind) {
        do {
            devices.append(deviceInfo);
        } while (BluetoothFindNextDevice(hFind, &deviceInfo));

        BluetoothFindDeviceClose(hFind);
    }

    return devices;
}

bool Lab6Window::connectToDevice(BTH_ADDR deviceAddr)
{
    m_clientSocket = socket(AF_BTH, SOCK_STREAM, BTHPROTO_RFCOMM);
    if (m_clientSocket == INVALID_SOCKET) {
        logMessage("❌ Ошибка создания клиентского сокета: " + QString::number(WSAGetLastError()));
        return false;
    }

    SOCKADDR_BTH sockAddr = { 0 };
    sockAddr.addressFamily = AF_BTH;
    sockAddr.btAddr = deviceAddr;


    bool connected = false;
    QVector<int> ports = {4, 1, 2, 3, 5};

    for (int port : ports) {
        sockAddr.port = port;
        logMessage("🔄 Попытка подключения к порту " + QString::number(port));

        if (::connect(m_clientSocket, (SOCKADDR*)&sockAddr, sizeof(sockAddr)) == 0) {
            logMessage("✅ Успешно подключено к порту " + QString::number(port));
            connected = true;
            break;
        }

        int error = WSAGetLastError();
        if (error != WSAECONNREFUSED) {
            logMessage("❌ Ошибка подключения к порту " + QString::number(port) + ": " + QString::number(error));
        }

        closesocket(m_clientSocket);
        m_clientSocket = socket(AF_BTH, SOCK_STREAM, BTHPROTO_RFCOMM);
        if (m_clientSocket == INVALID_SOCKET) break;
    }

    if (!connected) {
        logMessage("❌ Не удалось подключиться ни к одному порту");
        closesocket(m_clientSocket);
        m_clientSocket = INVALID_SOCKET;
        return false;
    }

    DWORD timeout = 15000;
    setsockopt(m_clientSocket, SOL_SOCKET, SO_RCVTIMEO, (char*)&timeout, sizeof(timeout));
    setsockopt(m_clientSocket, SOL_SOCKET, SO_SNDTIMEO, (char*)&timeout, sizeof(timeout));

    return true;
}

void Lab6Window::onScanDevicesClicked()
{
    if (m_isScanning) {
        logMessage("⚠️ Сканирование уже выполняется...");
        return;
    }

    if (!isBluetoothEnabled()) {
        QMessageBox::warning(this, "Bluetooth отключен",
                             "❌ Bluetooth неактивен!\n\n"
                             "Для работы приложения:\n"
                             "• Включите Bluetooth на этом компьютере\n"
                             "• Убедитесь, что адаптер работает\n"
                             "• Разрешите обнаружение устройства\n"
                             "• Проверьте драйверы Bluetooth");
        return;
    }

    logMessage("🔍 Начало сканирования REAL Bluetooth устройств...");
    m_devicesList->clear();
    m_progressBar->setValue(0);

    m_scanThread = new std::thread(&Lab6Window::scanBluetoothDevices, this);
}

void Lab6Window::scanBluetoothDevices()
{
    m_isScanning = true;
    showBluetoothAnimation(true);

    QMetaObject::invokeMethod(m_scanButton, "setEnabled", Qt::QueuedConnection, Q_ARG(bool, false));
    QMetaObject::invokeMethod(this, [this]() {
        logMessage("🔄 Сканирование сети Bluetooth...");
    }, Qt::QueuedConnection);

    try {
        auto devices = enumerateBluetoothDevices();
        int deviceCount = devices.size();

        QMetaObject::invokeMethod(this, [this, deviceCount]() {
            logMessage(QString("📊 Найдено REAL устройств в сети: %1").arg(deviceCount));
        }, Qt::QueuedConnection);

        for (int i = 0; i < deviceCount; ++i) {
            if (!m_isScanning) break;

            const BLUETOOTH_DEVICE_INFO& deviceInfo = devices[i];
            wstring deviceName(deviceInfo.szName);
            QString qDeviceName = QString::fromStdWString(deviceName);
            BTH_ADDR deviceAddr = deviceInfo.Address.ullLong;

            if (qDeviceName.isEmpty()) {
                qDeviceName = "Неизвестное устройство";
            }

            QString connectionStatus = deviceInfo.fConnected ? " 🔗 ПОДКЛЮЧЕНО" : " 📶 доступно";
            QString rememberedStatus = deviceInfo.fRemembered ? " (запомнено)" : " (новое)";
            QString deviceType = "";

            if (qDeviceName.contains("phone", Qt::CaseInsensitive) ||
                qDeviceName.contains("iphone", Qt::CaseInsensitive) ||
                qDeviceName.contains("samsung", Qt::CaseInsensitive)) {
                deviceType = " 📱";
            } else if (qDeviceName.contains("laptop", Qt::CaseInsensitive) ||
                       qDeviceName.contains("notebook", Qt::CaseInsensitive) ||
                       qDeviceName.contains("thinkpad", Qt::CaseInsensitive)) {
                deviceType = " 💻";
            } else if (qDeviceName.contains("headset", Qt::CaseInsensitive) ||
                       qDeviceName.contains("headphone", Qt::CaseInsensitive)) {
                deviceType = " 🎧";
            } else if (qDeviceName.contains("speaker", Qt::CaseInsensitive)) {
                deviceType = " 🔈";
            }

            QMetaObject::invokeMethod(this, [this, qDeviceName, deviceAddr, connectionStatus, rememberedStatus, deviceType]() {
                QString displayText = deviceType + " " + qDeviceName + connectionStatus + rememberedStatus +
                                      "\n   MAC: " + QString::number(deviceAddr, 16).toUpper();

                QListWidgetItem* item = new QListWidgetItem(displayText);
                item->setData(Qt::UserRole, QVariant::fromValue(deviceAddr));
                m_devicesList->addItem(item);

                logMessage("✅ Обнаружено: " + qDeviceName + connectionStatus);
            }, Qt::QueuedConnection);

            int progress = ((i + 1) * 100) / max(deviceCount, 1);
            QMetaObject::invokeMethod(m_progressBar, "setValue", Qt::QueuedConnection, Q_ARG(int, progress));

            this_thread::sleep_for(chrono::milliseconds(300));
        }

        QMetaObject::invokeMethod(this, [this, deviceCount]() {
            if (deviceCount == 0) {
                logMessage("❌ REAL Bluetooth устройства не найдены");
                logMessage("💡 Совет: Убедитесь, что другие устройства включены и доступны для обнаружения");
            } else {
                logMessage(QString("🎉 Сканирование REAL устройств завершено. Найдено: %1").arg(deviceCount));
                startConnectionAnimation();
            }
            m_progressBar->setValue(0);
        }, Qt::QueuedConnection);

    } catch (const exception& e) {
        QMetaObject::invokeMethod(this, [this, e]() {
            logMessage(QString("💥 Ошибка сканирования REAL устройств: %1").arg(e.what()));
            m_progressBar->setValue(0);
        }, Qt::QueuedConnection);
    }

    QMetaObject::invokeMethod(m_scanButton, "setEnabled", Qt::QueuedConnection, Q_ARG(bool, true));
    m_isScanning = false;
    showBluetoothAnimation(false);
}

void Lab6Window::onSendFileClicked()
{
    if (m_selectedDeviceAddr == 0) {
        QMessageBox::warning(this, "Устройство не выбрано",
                             "⚠️ Сначала выберите REAL устройство из списка\n\n"
                             "Для этого:\n"
                             "1. Нажмите 'Сканировать REAL устройства'\n"
                             "2. Дождитесь появления списка\n"
                             "3. Выберите нужное устройство щелчком мыши");
        return;
    }

    QString filePath = QFileDialog::getOpenFileName(this, "Выберите файл для отправки",
                                                    QDir::homePath(),
                                                    "Media Files (*.mp3 *.mp4 *.wav *.avi *.mkv *.mov *.wma);;"
                                                    "All Files (*.*)");
    if (filePath.isEmpty()) {
        return;
    }

    QFileInfo fileInfo(filePath);
    if (!fileInfo.exists()) {
        QMessageBox::warning(this, "Ошибка", "❌ Файл не существует!");
        return;
    }

    if (fileInfo.size() == 0) {
        QMessageBox::warning(this, "Ошибка", "❌ Файл пустой!");
        return;
    }

    logMessage("🚀 REAL отправка файла: " + fileInfo.fileName() +
               " (" + QString::number(fileInfo.size() / 1024) + " KB)");
    m_progressBar->setValue(0);

    QMetaObject::invokeMethod(m_sendButton, "setEnabled", Qt::QueuedConnection, Q_ARG(bool, false));

    m_transferThread = new std::thread([this, filePath]() {
        bool success = sendFile(filePath);
        QMetaObject::invokeMethod(this, [this, success]() {
            if (success) {
                logMessage("🎉 REAL передача файла УСПЕШНО завершена!");
                logMessage("💡 Приложение остается открытым - можно отправлять еще файлы!");
                startConnectionAnimation();
            } else {
                logMessage("💥 REAL передача файла ПРОВАЛИЛАСЬ!");
                logMessage("💡 Приложение остается открытым - попробуйте снова!");
            }
            m_progressBar->setValue(0);
            QMetaObject::invokeMethod(m_sendButton, "setEnabled", Qt::QueuedConnection, Q_ARG(bool, true));
        }, Qt::QueuedConnection);
    });
}

bool Lab6Window::sendFile(const QString& filePath)
{
    return sendFileWithProtocol(filePath);
}

bool Lab6Window::sendFileWithProtocol(const QString& filePath)
{
    m_isTransferring = true;
    showBluetoothAnimation(true);

    try {
        logMessage("🔗 Установка REAL Bluetooth соединения...");
        if (!connectToDevice(m_selectedDeviceAddr)) {
            logMessage("❌ Не удалось подключиться к устройству");
            return false;
        }

        QFile file(filePath);
        if (!file.open(QIODevice::ReadOnly)) {
            logMessage("❌ Ошибка открытия файла: " + filePath);
            closesocket(m_clientSocket);
            m_clientSocket = INVALID_SOCKET;
            return false;
        }

        qint64 fileSize = file.size();
        QByteArray fileData = file.readAll();
        file.close();

        logMessage("📊 Начало REAL передачи файла: " +
                   QString::number(fileSize) + " байт");

        const char startSignal = 'S';
        logMessage("📤 Отправка сигнала начала передачи...");

        if (::send(m_clientSocket, &startSignal, 1, 0) != 1) {
            logMessage("❌ Ошибка отправки сигнала начала");
            closesocket(m_clientSocket);
            m_clientSocket = INVALID_SOCKET;
            return false;
        }

        logMessage("⏳ Ожидание подтверждения от сервера...");
        char ack;

        fd_set readSet;
        FD_ZERO(&readSet);
        FD_SET(m_clientSocket, &readSet);

        struct timeval tv;
        tv.tv_sec = 10;
        tv.tv_usec = 0;

        int selectResult = select(0, &readSet, nullptr, nullptr, &tv);

        if (selectResult == 0) {
            logMessage("⏰ Таймаут ожидания подтверждения от сервера");
            logMessage("💡 Убедитесь, что сервер запущен на принимающем устройстве");
            closesocket(m_clientSocket);
            m_clientSocket = INVALID_SOCKET;
            return false;
        } else if (selectResult == SOCKET_ERROR) {
            logMessage("❌ Ошибка при ожидании подтверждения: " + QString::number(WSAGetLastError()));
            closesocket(m_clientSocket);
            m_clientSocket = INVALID_SOCKET;
            return false;
        }

        int bytesReceived = ::recv(m_clientSocket, &ack, 1, 0);
        if (bytesReceived != 1 || ack != 'A') {
            logMessage("❌ Не получено подтверждение начала. Получено: " +
                       QString::number(bytesReceived) + " байт, код: " + QString(ack));
            closesocket(m_clientSocket);
            m_clientSocket = INVALID_SOCKET;
            return false;
        }

        logMessage("✅ Сервер готов к приему файла!");

        QFileInfo fileInfo(filePath);
        QString fileName = fileInfo.fileName();
        QByteArray fileNameData = fileName.toUtf8();

        uint32_t nameLength = fileNameData.size();
        vector<char> nameLengthBuffer(sizeof(uint32_t));
        memcpy(nameLengthBuffer.data(), &nameLength, sizeof(uint32_t));

        if (::send(m_clientSocket, nameLengthBuffer.data(), sizeof(uint32_t), 0) != sizeof(uint32_t)) {
            logMessage("❌ Ошибка отправки длины имени файла");
            closesocket(m_clientSocket);
            m_clientSocket = INVALID_SOCKET;
            return false;
        }

        if (::recv(m_clientSocket, &ack, 1, 0) != 1 || ack != 'B') {
            logMessage("❌ Не получено подтверждение длины имени");
            closesocket(m_clientSocket);
            m_clientSocket = INVALID_SOCKET;
            return false;
        }

        if (::send(m_clientSocket, fileNameData.constData(), nameLength, 0) != nameLength) {
            logMessage("❌ Ошибка отправки имени файла");
            closesocket(m_clientSocket);
            m_clientSocket = INVALID_SOCKET;
            return false;
        }

        if (::recv(m_clientSocket, &ack, 1, 0) != 1 || ack != 'C') {
            logMessage("❌ Не получено подтверждение имени файла");
            closesocket(m_clientSocket);
            m_clientSocket = INVALID_SOCKET;
            return false;
        }

        qint64 networkFileSize = fileSize;
        vector<char> sizeBuffer(sizeof(qint64));
        memcpy(sizeBuffer.data(), &networkFileSize, sizeof(qint64));

        if (::send(m_clientSocket, sizeBuffer.data(), sizeof(qint64), 0) != sizeof(qint64)) {
            logMessage("❌ Ошибка отправки размера файла");
            closesocket(m_clientSocket);
            m_clientSocket = INVALID_SOCKET;
            return false;
        }

        if (::recv(m_clientSocket, &ack, 1, 0) != 1 || ack != 'D') {
            logMessage("❌ Не получено подтверждение размера файла");
            closesocket(m_clientSocket);
            m_clientSocket = INVALID_SOCKET;
            return false;
        }

        logMessage("✅ Протокол установлен. Начинаем передачу данных...");

        const int CHUNK_SIZE = 8192;
        qint64 totalSent = 0;
        auto startTime = chrono::steady_clock::now();

        while (totalSent < fileSize && m_isTransferring) {
            qint64 remaining = fileSize - totalSent;
            qint64 chunkSize = qMin(remaining, (qint64)CHUNK_SIZE);

            const char* chunkData = fileData.constData() + totalSent;
            int bytesSent = ::send(m_clientSocket, chunkData, chunkSize, 0);

            if (bytesSent == SOCKET_ERROR) {
                int error = WSAGetLastError();
                logMessage("❌ Ошибка отправки данных: " + QString::number(error));
                break;
            }

            totalSent += bytesSent;
            int progress = (totalSent * 100) / fileSize;

            auto currentTime = chrono::steady_clock::now();
            auto elapsed = chrono::duration_cast<chrono::milliseconds>(currentTime - startTime).count();
            double speed = elapsed > 0 ? (totalSent / 1024.0) / (elapsed / 1000.0) : 0;

            QMetaObject::invokeMethod(this, [this, progress, totalSent, speed]() {
                m_progressBar->setValue(progress);
                m_progressBar->setFormat(QString("Отправка: %1% (%2 KB, %3 KB/с)")
                                             .arg(progress)
                                             .arg(totalSent / 1024)
                                             .arg(speed, 0, 'f', 1));
            }, Qt::QueuedConnection);

            this_thread::sleep_for(chrono::milliseconds(5));
        }

        const char endSignal = 'E';
        ::send(m_clientSocket, &endSignal, 1, 0);

        if (::recv(m_clientSocket, &ack, 1, 0) == 1 && ack == 'F') {
            logMessage("✅ Сервер подтвердил успешный прием файла");
        }

        closesocket(m_clientSocket);
        m_clientSocket = INVALID_SOCKET;

        auto endTime = chrono::steady_clock::now();
        auto totalTime = chrono::duration_cast<chrono::milliseconds>(endTime - startTime).count();
        double avgSpeed = totalTime > 0 ? (totalSent / 1024.0) / (totalTime / 1000.0) : 0;

        logMessage("✅ REAL передача завершена. Отправлено: " +
                   QString::number(totalSent) + " байт за " +
                   QString::number(totalTime / 1000.0, 'f', 1) + " сек");

        return totalSent == fileSize;

    } catch (const exception& e) {
        logMessage(QString("💥 Ошибка REAL отправки файла: %1").arg(e.what()));
        if (m_clientSocket != INVALID_SOCKET) {
            closesocket(m_clientSocket);
            m_clientSocket = INVALID_SOCKET;
        }
        return false;
    }

    m_isTransferring = false;
    showBluetoothAnimation(false);
}

void Lab6Window::onReceiveFileClicked()
{
    if (m_isReceiving) {
        logMessage("⚠️ Сервер уже запущен и ожидает подключений");
        return;
    }

    logMessage("🔄 Запуск REAL Bluetooth сервера для приема файлов...");
    m_progressBar->setValue(0);

    QMetaObject::invokeMethod(m_receiveButton, "setEnabled", Qt::QueuedConnection, Q_ARG(bool, false));
    QMetaObject::invokeMethod(m_receiveButton, "setText", Qt::QueuedConnection, Q_ARG(QString, "🛑 Остановить сервер"));

    m_serverThread = new std::thread(&Lab6Window::startBluetoothServer, this);
}

void Lab6Window::startBluetoothServer()
{
    m_isReceiving = true;
    showBluetoothAnimation(true);

    try {
        m_serverSocket = socket(AF_BTH, SOCK_STREAM, BTHPROTO_RFCOMM);
        if (m_serverSocket == INVALID_SOCKET) {
            logMessage("❌ Ошибка создания серверного сокета: " + QString::number(WSAGetLastError()));
            return;
        }

        SOCKADDR_BTH sockAddr = { 0 };
        sockAddr.addressFamily = AF_BTH;

        bool bound = false;
        QVector<int> ports = {4, 1, 2, 3, 5};

        for (int port : ports) {
            sockAddr.port = port;
            logMessage("🔄 Попытка занять порт " + QString::number(port));

            if (::bind(m_serverSocket, (SOCKADDR*)&sockAddr, sizeof(sockAddr)) == 0) {
                logMessage("✅ Сервер запущен на порту " + QString::number(port));
                bound = true;
                break;
            }

            logMessage("❌ Порт " + QString::number(port) + " занят, пробуем следующий...");
        }

        if (!bound) {
            logMessage("💥 Не удалось занять ни один порт");
            closesocket(m_serverSocket);
            m_serverSocket = INVALID_SOCKET;
            return;
        }

        int addrLen = sizeof(sockAddr);
        if (::getsockname(m_serverSocket, (SOCKADDR*)&sockAddr, &addrLen) == SOCKET_ERROR) {
            logMessage("⚠️ Ошибка получения порта: " + QString::number(WSAGetLastError()));
        }

        logMessage("📡 REAL Bluetooth сервер запущен. Порт: " + QString::number(sockAddr.port));
        logMessage("⏳ Ожидание подключений от других устройств...");

        if (::listen(m_serverSocket, 1) == SOCKET_ERROR) {
            logMessage("❌ Ошибка прослушивания: " + QString::number(WSAGetLastError()));
            closesocket(m_serverSocket);
            m_serverSocket = INVALID_SOCKET;
            return;
        }

        fd_set readSet;
        FD_ZERO(&readSet);
        FD_SET(m_serverSocket, &readSet);

        struct timeval timeout;
        timeout.tv_sec = 30;
        timeout.tv_usec = 0;

        logMessage("⏰ Ожидание подключения (таймаут 30 сек)...");

        int selectResult = select(0, &readSet, nullptr, nullptr, &timeout);
        if (selectResult == 0) {
            logMessage("⏰ Таймаут ожидания подключения. Сервер остановлен.");
            closesocket(m_serverSocket);
            m_serverSocket = INVALID_SOCKET;
            return;
        } else if (selectResult == SOCKET_ERROR) {
            logMessage("❌ Ошибка select: " + QString::number(WSAGetLastError()));
            closesocket(m_serverSocket);
            m_serverSocket = INVALID_SOCKET;
            return;
        }

        SOCKADDR_BTH clientAddr = { 0 };
        int clientAddrSize = sizeof(clientAddr);

        SOCKET clientSocket = ::accept(m_serverSocket, (SOCKADDR*)&clientAddr, &clientAddrSize);
        if (clientSocket == INVALID_SOCKET) {
            logMessage("❌ Ошибка принятия подключения: " + QString::number(WSAGetLastError()));
            closesocket(m_serverSocket);
            m_serverSocket = INVALID_SOCKET;
            return;
        }

        logMessage("🎉 REAL устройство подключилось! MAC: " +
                   QString::number(clientAddr.btAddr, 16).toUpper());
        startConnectionAnimation();

        m_clientSocket = clientSocket;

        bool success = receiveFile();

        if (success) {
            logMessage("✅ REAL файл успешно принят и сохранен!");

            if (!m_receivedFilePath.isEmpty()) {
                logMessage("🎬 Запуск автоматического воспроизведения...");
                bool playSuccess = autoPlayFile(m_receivedFilePath);
                if (playSuccess) {
                    logMessage("🎵 Автовоспроизведение УСПЕШНО запущено!");
                } else {
                    logMessage("⚠️ Автовоспроизведение НЕ УДАЛОСЬ, но файл сохранен");
                }
            }

            logMessage("💡 Приложение остается открытым - можно принимать еще файлы!");
            logMessage("💡 Для приема следующего файла снова нажмите 'Запустить сервер приема'");
        } else {
            logMessage("💥 Ошибка приема файла");
            logMessage("💡 Приложение остается открытым - попробуйте снова!");
        }

        closesocket(clientSocket);
        m_clientSocket = INVALID_SOCKET;

    } catch (const exception& e) {
        logMessage(QString("💥 Ошибка REAL сервера: %1").arg(e.what()));
    }

    if (m_serverSocket != INVALID_SOCKET) {
        closesocket(m_serverSocket);
        m_serverSocket = INVALID_SOCKET;
    }

    m_isReceiving = false;
    showBluetoothAnimation(false);

    QMetaObject::invokeMethod(m_receiveButton, "setEnabled", Qt::QueuedConnection, Q_ARG(bool, true));
    QMetaObject::invokeMethod(m_receiveButton, "setText", Qt::QueuedConnection, Q_ARG(QString, "📥 Запустить сервер приема"));
}

bool Lab6Window::receiveFile()
{
    return receiveFileWithProtocol();
}

bool Lab6Window::receiveFileWithProtocol()
{
    try {
        logMessage("📥 Ожидание REAL передачи файла...");

        char signal;
        int bytesReceived = ::recv(m_clientSocket, &signal, 1, 0);
        if (bytesReceived != 1 || signal != 'S') {
            logMessage("❌ Не получен сигнал начала передачи");
            return false;
        }

        char ack = 'A';
        ::send(m_clientSocket, &ack, 1, 0);

        uint32_t nameLength;
        bytesReceived = ::recv(m_clientSocket, (char*)&nameLength, sizeof(uint32_t), 0);
        if (bytesReceived != sizeof(uint32_t)) {
            logMessage("❌ Ошибка получения длины имени файла");
            return false;
        }

        ack = 'B';
        ::send(m_clientSocket, &ack, 1, 0);

        QByteArray fileNameBuffer(nameLength, 0);
        bytesReceived = ::recv(m_clientSocket, fileNameBuffer.data(), nameLength, 0);
        if (bytesReceived != nameLength) {
            logMessage("❌ Ошибка получения имени файла");
            return false;
        }

        QString fileName = QString::fromUtf8(fileNameBuffer);

        ack = 'C';
        ::send(m_clientSocket, &ack, 1, 0);

        logMessage("📝 Прием файла: " + fileName);

        qint64 fileSize;
        bytesReceived = ::recv(m_clientSocket, (char*)&fileSize, sizeof(qint64), 0);
        if (bytesReceived != sizeof(qint64)) {
            logMessage("❌ Ошибка получения размера файла");
            return false;
        }

        ack = 'D';
        ::send(m_clientSocket, &ack, 1, 0);

        logMessage("📊 Размер файла: " + QString::number(fileSize) + " байт");

        QString receivedDir = QDir::currentPath() + "/received_bluetooth_files";
        QDir().mkpath(receivedDir);

        m_receivedFilePath = receivedDir + "/" + fileName;

        QFile file(m_receivedFilePath);
        if (!file.open(QIODevice::WriteOnly)) {
            logMessage("❌ Ошибка создания файла: " + m_receivedFilePath);
            return false;
        }

        const int CHUNK_SIZE = 8192;
        QByteArray buffer;
        buffer.resize(CHUNK_SIZE);

        qint64 totalReceived = 0;
        auto startTime = chrono::steady_clock::now();

        while (totalReceived < fileSize && m_isReceiving) {
            qint64 remaining = fileSize - totalReceived;
            qint64 chunkSize = qMin(remaining, (qint64)CHUNK_SIZE);

            bytesReceived = ::recv(m_clientSocket, buffer.data(), chunkSize, 0);

            if (bytesReceived <= 0) {
                logMessage("❌ Ошибка приема данных: " + QString::number(WSAGetLastError()));
                break;
            }

            file.write(buffer.data(), bytesReceived);
            totalReceived += bytesReceived;

            int progress = (totalReceived * 100) / fileSize;

            auto currentTime = chrono::steady_clock::now();
            auto elapsed = chrono::duration_cast<chrono::milliseconds>(currentTime - startTime).count();
            double speed = elapsed > 0 ? (totalReceived / 1024.0) / (elapsed / 1000.0) : 0;

            QMetaObject::invokeMethod(this, [this, progress, totalReceived, speed]() {
                m_progressBar->setValue(progress);
                m_progressBar->setFormat(QString("Прием: %1% (%2 KB, %3 KB/с)")
                                             .arg(progress)
                                             .arg(totalReceived / 1024)
                                             .arg(speed, 0, 'f', 1));
            }, Qt::QueuedConnection);
        }

        file.close();

        if (::recv(m_clientSocket, &signal, 1, 0) == 1 && signal == 'E') {
            ack = 'F';
            ::send(m_clientSocket, &ack, 1, 0);
            logMessage("✅ Передача файла завершена успешно");
        }

        auto endTime = chrono::steady_clock::now();
        auto totalTime = chrono::duration_cast<chrono::milliseconds>(endTime - startTime).count();
        double avgSpeed = totalTime > 0 ? (totalReceived / 1024.0) / (totalTime / 1000.0) : 0;

        logMessage("✅ REAL прием завершен. Получено: " +
                   QString::number(totalReceived) + " байт за " +
                   QString::number(totalTime / 1000.0, 'f', 1) + " сек");

        logMessage("💾 Файл сохранен: " + m_receivedFilePath);

        return totalReceived == fileSize;

    } catch (const exception& e) {
        logMessage(QString("💥 Ошибка REAL приема файла: %1").arg(e.what()));
        return false;
    }
}

bool Lab6Window::autoPlayFile(const QString& filePath)
{
    QFileInfo fileInfo(filePath);
    if (!fileInfo.exists()) {
        logMessage("❌ Файл для воспроизведения не существует: " + filePath);
        return false;
    }

    QString extension = fileInfo.suffix().toLower();
    logMessage("🎵 Автовоспроизведение файла: " + fileInfo.fileName());

    QString finalFilePath = detectFileTypeAndRename(filePath) ? m_receivedFilePath : filePath;

    logMessage("🚀 Запуск воспроизведения: " + finalFilePath);

    bool success = false;

    success = QDesktopServices::openUrl(QUrl::fromLocalFile(finalFilePath));

    if (!success) {
#ifdef Q_OS_WIN
        QString command = "start \"\" \"" + finalFilePath + "\"";
        success = (system(command.toUtf8().constData()) == 0);
#endif
    }

    if (success) {
        logMessage("✅ Автовоспроизведение УСПЕШНО запущено!");
        logMessage("🎵 Файл открыт в ассоциированной программе");
        logMessage("💡 Приложение остается открытым - можно принимать еще файлы!");
    } else {
        logMessage("⚠️ Автовоспроизведение НЕ УДАЛОСЬ запустить автоматически");
        logMessage("💡 Файл сохранен по пути: " + finalFilePath);
        logMessage("💡 Откройте файл вручную в медиаплеере");
        logMessage("💡 Приложение остается открытым - можно принимать еще файлы!");
    }

    return success;
}

bool Lab6Window::detectFileTypeAndRename(const QString& filePath)
{
    QFile file(filePath);
    if (!file.open(QIODevice::ReadOnly)) {
        return false;
    }

    QByteArray header = file.read(12);
    file.close();

    QString newExtension;

    if (header.startsWith("ID3") || header.startsWith("\xFF\xFB") || header.startsWith("\x49\x44\x33")) {
        newExtension = "mp3";
    } else if (header.startsWith("\x00\x00\x00") && header.size() > 8 &&
               (header[4] == 'f' && header[5] == 't' && header[6] == 'y' && header[7] == 'p')) {
        newExtension = "mp4";
    } else if (header.startsWith("RIFF") && header.size() > 8 &&
               (header[8] == 'W' && header[9] == 'A' && header[10] == 'V' && header[11] == 'E')) {
        newExtension = "wav";
    } else if (header.startsWith("OggS")) {
        newExtension = "ogg";
    } else if (header.startsWith("\x1A\x45\xDF\xA3")) {
        newExtension = "mkv";
    } else {
        return false;
    }

    QFileInfo oldInfo(filePath);
    QString newFilePath = oldInfo.path() + "/" + oldInfo.completeBaseName() + "." + newExtension;

    if (QFile::rename(filePath, newFilePath)) {
        m_receivedFilePath = newFilePath;
        logMessage("📝 Файл переименован в: " + newFilePath);
        return true;
    }

    return false;
}

void Lab6Window::stopBluetoothServer()
{
    m_isReceiving = false;
    m_isTransferring = false;
    m_isScanning = false;

    if (m_clientSocket != INVALID_SOCKET) {
        closesocket(m_clientSocket);
        m_clientSocket = INVALID_SOCKET;
    }

    if (m_serverSocket != INVALID_SOCKET) {
        closesocket(m_serverSocket);
        m_serverSocket = INVALID_SOCKET;
    }

    logMessage("🛑 REAL Bluetooth сервер остановлен");
}

void Lab6Window::onBackClicked()
{
    stopBluetoothServer();
    emit backToMain();
    close();
}

void Lab6Window::onDeviceSelected(QListWidgetItem* item)
{
    if (item) {
        m_selectedDevice = item->text();
        BTH_ADDR deviceAddr = item->data(Qt::UserRole).toULongLong();
        m_selectedDeviceAddr = deviceAddr;

        logMessage("✅ Выбрано устройство: " + m_selectedDevice.split('\n').first());
        logMessage("   MAC-адрес: " + QString::number(deviceAddr, 16).toUpper());
    }
}

void Lab6Window::updateBluetoothStatus()
{
    if (isBluetoothEnabled()) {
        QString radioInfo = getBluetoothRadioInfo();
        m_statusLabel->setText("✅ Bluetooth АКТИВЕН\n" + radioInfo.split('\n').first());
        m_statusLabel->setStyleSheet("color: green; background-color: rgba(0,255,0,0.1); border: 2px solid green; border-radius: 6px; padding: 8px; font-size: 11px;");
    } else {
        m_statusLabel->setText("❌ Bluetooth НЕАКТИВЕН\nВключите Bluetooth адаптер");
        m_statusLabel->setStyleSheet("color: red; background-color: rgba(255,0,0,0.1); border: 2px solid red; border-radius: 6px; padding: 8px; font-size: 11px;");
    }
}

void Lab6Window::showBluetoothAnimation(bool show)
{
    QMetaObject::invokeMethod(this, [this, show]() {
        if (m_characterAnimation) {
            if (show) {
                startTransferAnimation();
            } else {
                stopTransferAnimation();
            }
        }
    }, Qt::QueuedConnection);
}

void Lab6Window::logMessage(const QString &message)
{
    QString timestamp = QDateTime::currentDateTime().toString("hh:mm:ss");
    m_logText->append(QString("[%1] %2").arg(timestamp, message));

    QScrollBar *scrollBar = m_logText->verticalScrollBar();
    scrollBar->setValue(scrollBar->maximum());
}

void Lab6Window::updateProgress(int value)
{
    m_progressBar->setValue(value);
}

void Lab6Window::closeEvent(QCloseEvent *event)
{
    stopBluetoothServer();
    m_isScanning = false;
    m_isTransferring = false;
    m_isReceiving = false;
    QMainWindow::closeEvent(event);
}

void Lab6Window::resizeEvent(QResizeEvent *event)
{
    QMainWindow::resizeEvent(event);
    updateAnimationPosition();
}

void Lab6Window::showEvent(QShowEvent *event)
{
    QMainWindow::showEvent(event);
    updateAnimationPosition();
    updateBluetoothStatus();
}
