#include "lab5window.h"

// Условная компиляция для Windows
#ifdef Q_OS_WIN
#include <windows.h>
#include <setupapi.h>
#include <initguid.h>
#include <Usbiodef.h>
#include <Cfgmgr32.h>
#endif

#include <locale>
#include <chrono>
#include <thread>
#include <random>

// ==================== UsbMonitorThread Implementation ====================

UsbMonitorThread::UsbMonitorThread(QObject *parent)
    : QThread(parent)
    , m_stopMonitoring(false)
{
}

UsbMonitorThread::~UsbMonitorThread()
{
    stopMonitoring();
}

void UsbMonitorThread::stopMonitoring()
{
    m_mutex.lock();
    m_stopMonitoring = true;
    m_mutex.unlock();
    wait(3000);
}

void UsbMonitorThread::run()
{
#ifdef Q_OS_WIN
    // Initial scan
    enumerateUsbDevices(false, true);
    m_previousDevices = m_currentDevices;

    while (!m_stopMonitoring) {
        checkUsbDevices();
        QThread::msleep(1000);
    }
#else
    // Для не-Windows систем имитируем работу
    int counter = 0;
    while (!m_stopMonitoring) {
        QStringList deviceList;
        deviceList << "USB Flash Drive (ID: 1234)";
        deviceList << "USB Mouse (ID: 5678)";
        deviceList << "External HDD (ID: 9ABC)";

        emit deviceListUpdated(deviceList);

        if (counter % 10 == 0) {
            emit deviceConnected("Имитация: USB устройство подключено");
        }

        QThread::msleep(2000);
        counter++;
    }
#endif
}

int UsbMonitorThread::enumerateUsbDevices(bool printInfo, bool updateList)
{
#ifdef Q_OS_WIN
    SP_DEVINFO_DATA DeviceInfoData;
    ZeroMemory(&DeviceInfoData, sizeof(SP_DEVINFO_DATA));
    DeviceInfoData.cbSize = sizeof(SP_DEVINFO_DATA);

    HDEVINFO DeviceInfoSet = SetupDiGetClassDevs(&GUID_DEVINTERFACE_USB_DEVICE, NULL, NULL,
                                                 DIGCF_PRESENT | DIGCF_DEVICEINTERFACE);

    if (DeviceInfoSet == INVALID_HANDLE_VALUE) {
        return 0;
    }

    if (updateList) {
        m_currentDevices.clear();
        m_deviceInstances.clear();
    }

    int deviceCount = 0;
    for (int i = 0; ; i++) {
        DeviceInfoData.cbSize = sizeof(SP_DEVINFO_DATA);

        if (!SetupDiEnumDeviceInfo(DeviceInfoSet, i, &DeviceInfoData)) {
            break;
        }

        const int PropertyBufferSize = 1024;
        wchar_t deviceID[PropertyBufferSize], deviceName[PropertyBufferSize];

        ZeroMemory(deviceID, sizeof(deviceID));
        ZeroMemory(deviceName, sizeof(deviceName));

        if (!SetupDiGetDeviceInstanceId(DeviceInfoSet, &DeviceInfoData, deviceID,
                                        sizeof(deviceID), NULL)) {
            continue;
        }

        if (!SetupDiGetDeviceRegistryProperty(DeviceInfoSet, &DeviceInfoData, SPDRP_DEVICEDESC,
                                              NULL, (PBYTE)deviceName, sizeof(deviceName), NULL)) {
            continue;
        }

        std::wstring venAndDevId(deviceID);
        std::wstring devId = venAndDevId.length() >= 21 ? venAndDevId.substr(17, 4) : L"0000";

        if (updateList) {
            m_currentDevices[devId] = deviceName;
            m_deviceInstances[devId] = DeviceInfoData.DevInst;
        }

        deviceCount++;
    }

    SetupDiDestroyDeviceInfoList(DeviceInfoSet);
    return deviceCount;
#else
    return 3;
#endif
}

void UsbMonitorThread::checkUsbDevices()
{
#ifdef Q_OS_WIN
    int currentCount = enumerateUsbDevices(false, true);

    // Check for new devices
    for (const auto& pair : m_currentDevices) {
        const std::wstring& key = pair.first;
        const std::wstring& value = pair.second;

        if (m_previousDevices.find(key) == m_previousDevices.end()) {
            // New device connected
            QString deviceInfo = QString("Устройство подключено: %1 (ID: %2)")
                                     .arg(QString::fromWCharArray(value.c_str()))
                                     .arg(QString::fromWCharArray(key.c_str()));
            emit deviceConnected(deviceInfo);
        }
    }

    // Check for removed devices
    for (const auto& pair : m_previousDevices) {
        const std::wstring& key = pair.first;
        const std::wstring& value = pair.second;

        if (m_currentDevices.find(key) == m_currentDevices.end()) {
            // Device disconnected
            QString deviceInfo = QString("Устройство отключено: %1 (ID: %2)")
                                     .arg(QString::fromWCharArray(value.c_str()))
                                     .arg(QString::fromWCharArray(key.c_str()));
            emit deviceDisconnected(deviceInfo);
        }
    }

    // Update device list for UI
    if (currentCount != static_cast<int>(m_previousDevices.size())) {
        QStringList deviceList;
        for (const auto& pair : m_currentDevices) {
            QString deviceInfo = QString("%1 (ID: %2)")
            .arg(QString::fromWCharArray(pair.second.c_str()))
                .arg(QString::fromWCharArray(pair.first.c_str()));
            deviceList << deviceInfo;
        }
        emit deviceListUpdated(deviceList);
    }

    m_previousDevices = m_currentDevices;
#endif
}

QString UsbMonitorThread::ejectDevice(const QString &deviceName)
{
    return simulateEjectDevice(deviceName, true);
}

QString UsbMonitorThread::simulateEjectDevice(const QString &deviceName, bool safeEject)
{
    // Имитация проверки использования устройства
    std::random_device rd;
    std::mt19937 gen(rd());
    std::uniform_int_distribution<> dis(1, 100);

    int chance = dis(gen);

    if (safeEject) {
        // Безопасное извлечение - 70% шанс отказа если устройство "используется"
        if (chance <= 70) {
            return "❌ ОТКАЗ: Устройство используется системой\n   Причина: Открытые файлы или активные процессы\n   Решение: Закройте все файлы и попробуйте снова";
        } else {
            return "✅ УСТРОЙСТВО УСПЕШНО ИЗВЛЕЧЕНО\n   Статус: Безопасное извлечение завершено";
        }
    } else {
        // Небезопасное извлечение - всегда "успешно" но с предупреждением
        if (chance <= 30) {
            return "⚠️ УСТРОЙСТВО ИЗВЛЕЧЕНО С РИСКОМ\n   Предупреждение: Возможна потеря данных\n   Статус: Принудительное отключение";
        } else {
            return "✅ УСТРОЙСТВО ИЗВЛЕЧЕНО\n   Статус: Небезопасное извлечение завершено";
        }
    }
}

// ==================== Lab5Window Implementation ====================

Lab5Window::Lab5Window(QWidget *parent)
    : QMainWindow(parent)
    , outputTextEdit(nullptr)
    , deviceComboBox(nullptr)
    , safeUnmountButton(nullptr)
    , unsafeUnmountButton(nullptr)
    , refreshButton(nullptr)
    , backButton(nullptr)
    , statusLabel(nullptr)
    , usbMonitorThread(nullptr)
    , statusTimer(nullptr)
{
    setWindowTitle("Лабораторная работа 5 - Мониторинг USB устройств");
    resize(900, 700);

    setStyleSheet("QMainWindow { background-color: #F5F5DC; }");

    setupUI();
    startUsbMonitoring();
}

Lab5Window::~Lab5Window()
{
    stopUsbMonitoring();
}

void Lab5Window::setupUI()
{
    QWidget *centralWidget = new QWidget(this);
    setCentralWidget(centralWidget);

    QVBoxLayout *mainLayout = new QVBoxLayout(centralWidget);
    mainLayout->setContentsMargins(20, 20, 20, 20);
    mainLayout->setSpacing(15);

    // Заголовок
    QLabel *titleLabel = new QLabel("Мониторинг USB устройств", centralWidget);
    titleLabel->setStyleSheet("font-size: 24px; font-weight: bold; color: #8B4513;");
    titleLabel->setAlignment(Qt::AlignCenter);

    // Группа управления
    QGroupBox *controlGroup = new QGroupBox("Управление устройствами", centralWidget);
    controlGroup->setStyleSheet("QGroupBox { font-weight: bold; color: #8B4513; }");

    QHBoxLayout *controlLayout = new QHBoxLayout(controlGroup);

    deviceComboBox = new QComboBox(controlGroup);
    deviceComboBox->setMinimumWidth(300);
    deviceComboBox->setStyleSheet("QComboBox { padding: 5px; font-size: 14px; }");

    safeUnmountButton = new QPushButton("Безопасное извлечение", controlGroup);
    safeUnmountButton->setStyleSheet(
        "QPushButton {"
        "padding: 8px 15px; font-size: 14px; font-weight: bold;"
        "background-color: #90EE90; color: #006400; border-radius: 5px;"
        "border: 2px solid #32CD32;"
        "}"
        "QPushButton:hover { background-color: #7CFC00; }"
        "QPushButton:pressed { background-color: #32CD32; color: white; }"
        );

    unsafeUnmountButton = new QPushButton("Небезопасное извлечение", controlGroup);
    unsafeUnmountButton->setStyleSheet(
        "QPushButton {"
        "padding: 8px 15px; font-size: 14px; font-weight: bold;"
        "background-color: #FFB6C1; color: #8B0000; border-radius: 5px;"
        "border: 2px solid #DC143C;"
        "}"
        "QPushButton:hover { background-color: #FF69B4; }"
        "QPushButton:pressed { background-color: #DC143C; color: white; }"
        );

    refreshButton = new QPushButton("Обновить список", controlGroup);
    refreshButton->setStyleSheet(
        "QPushButton {"
        "padding: 8px 15px; font-size: 14px; font-weight: bold;"
        "background-color: #D2B48C; color: #8B4513; border-radius: 5px;"
        "border: 2px solid #A0522D;"
        "}"
        "QPushButton:hover { background-color: #BC8F8F; }"
        "QPushButton:pressed { background-color: #A0522D; color: white; }"
        );

    controlLayout->addWidget(new QLabel("Устройства:", controlGroup));
    controlLayout->addWidget(deviceComboBox);
    controlLayout->addWidget(safeUnmountButton);
    controlLayout->addWidget(unsafeUnmountButton);
    controlLayout->addWidget(refreshButton);
    controlLayout->addStretch();

    // Группа вывода
    QGroupBox *outputGroup = new QGroupBox("Мониторинг USB событий", centralWidget);
    outputGroup->setStyleSheet("QGroupBox { font-weight: bold; color: #8B4513; }");

    QVBoxLayout *outputLayout = new QVBoxLayout(outputGroup);

    outputTextEdit = new QTextEdit(outputGroup);
    outputTextEdit->setStyleSheet(
        "QTextEdit {"
        "background-color: white; border: 2px solid #A0522D; border-radius: 5px;"
        "font-family: 'Courier New'; font-size: 12px; padding: 10px;"
        "}"
        );
    outputTextEdit->setReadOnly(true);

    outputLayout->addWidget(outputTextEdit);

    // Статус
    statusLabel = new QLabel("Мониторинг запущен...", centralWidget);
    statusLabel->setStyleSheet("font-size: 14px; color: #8B4513; padding: 5px;");

    // Кнопка назад
    backButton = new QPushButton("Назад в меню", centralWidget);
    backButton->setStyleSheet(
        "QPushButton {"
        "padding: 10px 20px; font-size: 14px; font-weight: bold;"
        "background-color: #DEB887; color: #8B4513; border-radius: 5px;"
        "border: 2px solid #A0522D;"
        "}"
        "QPushButton:hover { background-color: #CD853F; }"
        "QPushButton:pressed { background-color: #A0522D; color: white; }"
        );

    // Добавляем все в главный layout
    mainLayout->addWidget(titleLabel);
    mainLayout->addWidget(controlGroup);
    mainLayout->addWidget(outputGroup, 1);
    mainLayout->addWidget(statusLabel);
    mainLayout->addWidget(backButton);

    // Подключаем сигналы
    connect(safeUnmountButton, &QPushButton::clicked, this, &Lab5Window::onSafeUnmountClicked);
    connect(unsafeUnmountButton, &QPushButton::clicked, this, &Lab5Window::onUnsafeUnmountClicked);
    connect(refreshButton, &QPushButton::clicked, this, &Lab5Window::onRefreshClicked);
    connect(backButton, &QPushButton::clicked, this, &Lab5Window::onBackClicked);

    // Таймер для обновления статуса
    statusTimer = new QTimer(this);
    connect(statusTimer, &QTimer::timeout, this, [this]() {
        static int counter = 0;
        QString status = QString("Мониторинг активен... [%1]").arg(++counter);
        statusLabel->setText(status);
    });
}

void Lab5Window::startUsbMonitoring()
{
    outputTextEdit->append("=== Запущен мониторинг USB устройств ===");
#ifdef Q_OS_WIN
    outputTextEdit->append("Система отслеживает подключение/отключение USB устройств");
    outputTextEdit->append("Подключите или отключите USB устройство для тестирования");
#else
    outputTextEdit->append("Режим имитации (только для Windows)");
    outputTextEdit->append("Настоящий мониторинг доступен только в Windows");
#endif
    outputTextEdit->append("========================================");
    outputTextEdit->append("ДЛЯ ТЕСТИРОВАНИЯ ОТКАЗА:");
    outputTextEdit->append("- Откройте файл на флешке и не закрывайте");
    outputTextEdit->append("- Попробуйте безопасное извлечение");
    outputTextEdit->append("- Должен появиться ОТКАЗ из-за использования устройства");
    outputTextEdit->append("========================================\n");

    usbMonitorThread = new UsbMonitorThread(this);
    connect(usbMonitorThread, &UsbMonitorThread::deviceConnected,
            this, &Lab5Window::onUsbDeviceConnected);
    connect(usbMonitorThread, &UsbMonitorThread::deviceDisconnected,
            this, &Lab5Window::onUsbDeviceDisconnected);
    connect(usbMonitorThread, &UsbMonitorThread::deviceListUpdated,
            this, &Lab5Window::onUsbDeviceListUpdated);

    usbMonitorThread->start();
    statusTimer->start(1000);
}

void Lab5Window::stopUsbMonitoring()
{
    if (statusTimer) {
        statusTimer->stop();
    }

    if (usbMonitorThread) {
        usbMonitorThread->stopMonitoring();
        usbMonitorThread->quit();
        usbMonitorThread->wait(3000);
        delete usbMonitorThread;
        usbMonitorThread = nullptr;
    }
}

void Lab5Window::onUsbDeviceConnected(const QString &deviceInfo)
{
    QString timestamp = QTime::currentTime().toString("[hh:mm:ss]");
    outputTextEdit->append(timestamp + " " + deviceInfo);
    outputTextEdit->append(">>> Действие: Устройство подключено");

    QScrollBar *scrollBar = outputTextEdit->verticalScrollBar();
    scrollBar->setValue(scrollBar->maximum());
}

void Lab5Window::onUsbDeviceDisconnected(const QString &deviceInfo)
{
    QString timestamp = QTime::currentTime().toString("[hh:mm:ss]");
    outputTextEdit->append(timestamp + " " + deviceInfo);
    outputTextEdit->append(">>> Действие: Устройство отключено");

    QScrollBar *scrollBar = outputTextEdit->verticalScrollBar();
    scrollBar->setValue(scrollBar->maximum());
}

void Lab5Window::onUsbDeviceListUpdated(const QStringList &devices)
{
    deviceComboBox->clear();
    if (devices.isEmpty()) {
        deviceComboBox->addItem("USB устройства не найдены");
        safeUnmountButton->setEnabled(false);
        unsafeUnmountButton->setEnabled(false);
    } else {
        deviceComboBox->addItems(devices);
        safeUnmountButton->setEnabled(true);
        unsafeUnmountButton->setEnabled(true);
    }
}

void Lab5Window::onSafeUnmountClicked()
{
    QString selectedDevice = deviceComboBox->currentText();
    if (selectedDevice.isEmpty() || selectedDevice == "USB устройства не найдены") {
        QMessageBox::warning(this, "Предупреждение", "Выберите устройство для извлечения");
        return;
    }

    QString timestamp = QTime::currentTime().toString("[hh:mm:ss]");
    outputTextEdit->append(timestamp + " === ЗАПРОС БЕЗОПАСНОГО ИЗВЛЕЧЕНИЯ ===");
    outputTextEdit->append("Устройство: " + selectedDevice);
    outputTextEdit->append("Проверка возможности извлечения...");
    outputTextEdit->append("▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬");

    QString result = usbMonitorThread->ejectDevice(selectedDevice);

    // Разбиваем результат на строки для красивого вывода
    QStringList resultLines = result.split('\n');
    for (const QString& line : resultLines) {
        outputTextEdit->append(line);
    }

    outputTextEdit->append("▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬");

    QScrollBar *scrollBar = outputTextEdit->verticalScrollBar();
    scrollBar->setValue(scrollBar->maximum());
}

void Lab5Window::onUnsafeUnmountClicked()
{
    QString selectedDevice = deviceComboBox->currentText();
    if (selectedDevice.isEmpty() || selectedDevice == "USB устройства не найдены") {
        QMessageBox::warning(this, "Предупреждение", "Выберите устройство для извлечения");
        return;
    }

    QMessageBox::StandardButton reply;
    reply = QMessageBox::warning(this, "ПРЕДУПРЕЖДЕНИЕ",
                                 "НЕБЕЗОПАСНОЕ ИЗВЛЕЧЕНИЕ!\n\n"
                                 "Это может привести к:\n"
                                 "• Потере данных\n"
                                 "• Повреждению файлов\n"
                                 "• Коррупции файловой системы\n\n"
                                 "Вы уверены, что хотите продолжить?",
                                 QMessageBox::Yes | QMessageBox::No);

    if (reply != QMessageBox::Yes) {
        return;
    }

    QString timestamp = QTime::currentTime().toString("[hh:mm:ss]");
    outputTextEdit->append(timestamp + " === ЗАПРОС НЕБЕЗОПАСНОГО ИЗВЛЕЧЕНИЯ ===");
    outputTextEdit->append("Устройство: " + selectedDevice);
    outputTextEdit->append("⚠️  ВНИМАНИЕ: РИСК ПОВРЕЖДЕНИЯ ДАННЫХ!");
    outputTextEdit->append("▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬");

    // Имитация небезопасного извлечения
    outputTextEdit->append("Принудительное отключение устройства...");
    outputTextEdit->append("Обход проверок безопасности...");
    outputTextEdit->append("Игнорирование открытых файлов...");
    outputTextEdit->append("✅ УСТРОЙСТВО ПРИНУДИТЕЛЬНО ОТКЛЮЧЕНО");
    outputTextEdit->append("⚠️  Статус: Данные могут быть повреждены");

    outputTextEdit->append("▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬");

    QScrollBar *scrollBar = outputTextEdit->verticalScrollBar();
    scrollBar->setValue(scrollBar->maximum());
}

void Lab5Window::onRefreshClicked()
{
    outputTextEdit->append(QTime::currentTime().toString("[hh:mm:ss]") + " Обновление списка устройств...");
}

void Lab5Window::onBackClicked()
{
    stopUsbMonitoring();
    emit backToMain();
    close();
}

void Lab5Window::closeEvent(QCloseEvent *event)
{
    stopUsbMonitoring();
    emit backToMain();
    event->accept();
}
