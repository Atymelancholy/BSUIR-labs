#include "lab5window.h"
#include "characteranimation.h"
#include "usbmanager.h"

#include <QListWidgetItem>
#include <QMessageBox>
#include <QVBoxLayout>
#include <QHBoxLayout>
#include <QPushButton>
#include <QLabel>
#include <QGroupBox>
#include <QListWidget>
#include <QTimer>
#include <QScreen>
#include <QGuiApplication>
#include <QDebug>
#include <QMetaObject>
#include <QMetaMethod>

Lab5Window::Lab5Window(QWidget *parent) :
    QMainWindow(parent),
    m_usbManager(new USBManager(this)),
    m_characterAnimation(nullptr),
    m_centralWidget(nullptr),
    m_devicesGroup(nullptr),
    m_infoGroup(nullptr),
    m_devicesList(nullptr),
    m_deviceInfoLabel(nullptr),
    m_statusLabel(nullptr),
    m_refreshButton(nullptr),
    m_ejectButton(nullptr),
    m_backButton(nullptr)
{
    setWindowTitle("Мониторинг USB устройств - Лабораторная работа 5");
    resize(900, 600);

    qDebug() << "Инициализация окна USB мониторинга";

    initializeInterface();
    setupSignalHandlers();
    applyCustomStyles();
    initializeCharacterAnimation();

    QTimer::singleShot(500, this, &Lab5Window::refreshDeviceList);
    QTimer::singleShot(100, this, &Lab5Window::centerOnScreen);
}

Lab5Window::~Lab5Window()
{
    delete m_characterAnimation;
    delete m_usbManager;
}

void Lab5Window::initializeInterface()
{
    setStyleSheet("QMainWindow { background-color: #F5F5DC; }");

    m_centralWidget = new QWidget(this);
    setCentralWidget(m_centralWidget);

    QVBoxLayout *mainLayout = new QVBoxLayout(m_centralWidget);
    mainLayout->setContentsMargins(20, 20, 20, 20);
    mainLayout->setSpacing(15);

    QHBoxLayout *contentLayout = new QHBoxLayout();
    contentLayout->setSpacing(20);

    setupDevicesPanel(contentLayout);
    setupInfoPanel(contentLayout);

    mainLayout->addLayout(contentLayout);

    initializeCharacterAnimation();
}

void Lab5Window::setupDevicesPanel(QHBoxLayout *parentLayout)
{
    m_devicesGroup = new QGroupBox("Список USB устройств", m_centralWidget);
    QVBoxLayout *devicesLayout = new QVBoxLayout(m_devicesGroup);

    m_devicesList = new QListWidget(m_devicesGroup);
    m_devicesList->setMinimumWidth(400);

    QHBoxLayout *controlButtonsLayout = new QHBoxLayout();
    m_refreshButton = new QPushButton("Обновить", m_devicesGroup);
    m_ejectButton = new QPushButton("Извлечь", m_devicesGroup);
    m_backButton = new QPushButton("В главное меню", m_devicesGroup);

    controlButtonsLayout->addWidget(m_refreshButton);
    controlButtonsLayout->addWidget(m_ejectButton);
    controlButtonsLayout->addStretch();
    controlButtonsLayout->addWidget(m_backButton);

    devicesLayout->addWidget(m_devicesList);
    devicesLayout->addLayout(controlButtonsLayout);

    parentLayout->addWidget(m_devicesGroup);
}

void Lab5Window::setupInfoPanel(QHBoxLayout *parentLayout)
{
    m_infoGroup = new QGroupBox("Свойства устройства", m_centralWidget);
    QVBoxLayout *infoLayout = new QVBoxLayout(m_infoGroup);

    m_deviceInfoLabel = new QLabel("Выберите устройство из списка", m_infoGroup);
    m_deviceInfoLabel->setWordWrap(true);
    m_deviceInfoLabel->setMinimumHeight(150);

    m_statusLabel = new QLabel("Ожидание действий", m_infoGroup);
    m_statusLabel->setAlignment(Qt::AlignCenter);
    m_statusLabel->setMinimumHeight(30);

    infoLayout->addWidget(m_deviceInfoLabel);
    infoLayout->addWidget(m_statusLabel);

    parentLayout->addWidget(m_infoGroup);
}

void Lab5Window::initializeCharacterAnimation()
{
    qDebug() << "Инициализация анимации USB мониторинга...";

    m_characterAnimation = new CharacterAnimation(this);
    m_characterAnimation->setFixedSize(150, 150);
    m_characterAnimation->setBackgroundColor(Qt::transparent);

    // Пробуем разные пути к спрайтам
    QStringList spritePaths = {
        "C:/Users/atyme/OneDrive/Документы/db/AnimationLab/resources/images/l5.png",
        ":/resources/images/l5.png",
        "resources/images/l5.png",
        "C:/Users/atyme/OneDrive/Документы/db/AnimationLab/resources/images/lab5.png",
        ":/resources/images/lab5.png",
        "resources/images/lab5.png",
        "C:/Users/atyme/OneDrive/Документы/db/AnimationLab/resources/images/usb_animation.png",
        ":/resources/images/usb_animation.png"
    };

    bool spriteLoaded = false;

    // Пробуем разные размеры кадров как в 4-й лабораторной
    QList<QPair<int, int>> frameSizes = {
        {1200, 680},  // Оригинальный размер
        {300, 340},  // В 2 раза меньше
        {200, 227},  // В 3 раза меньше
        {150, 170},  // В 4 раза меньше
        {100, 113},  // В 6 раз меньше
        {1130, 1130} // Как в 4-й лабораторной
    };

    for (const QString& path : spritePaths) {
        for (const auto& frameSize : frameSizes) {
            int frameWidth = frameSize.first;
            int frameHeight = frameSize.second;

            qDebug() << "Попытка загрузки:" << path << "с размером кадра:" << frameWidth << "x" << frameHeight;

            if (m_characterAnimation->loadSpriteSheet(path, frameWidth, frameHeight)) {
                spriteLoaded = true;
                qDebug() << "УСПЕХ: Спрайт загружен! Размер кадра:" << frameWidth << "x" << frameHeight;

                // Настройка анимации как в 4-й лабораторной
                m_characterAnimation->setScaleFactor(0.18); // Масштабирование как в камерной анимации
                m_characterAnimation->setAnimationSpeed(150); // Скорость анимации
                m_characterAnimation->setFixedSize(150, 150); // Фиксированный размер

                break;
            }
        }
        if (spriteLoaded) break;
    }

    if (!spriteLoaded) {
        qDebug() << "Не удалось загрузить анимацию. Создаем заглушку.";

        // Создаем информативную заглушку
        QWidget *debugWidget = new QWidget(this);
        debugWidget->setFixedSize(120, 120);
        debugWidget->setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #4A90E2, stop:1 #357ABD); border: 2px solid #2C5AA0; border-radius: 10px;");

        QLabel *debugLabel = new QLabel("USB\nMONITOR", debugWidget);
        debugLabel->setAlignment(Qt::AlignCenter);
        debugLabel->setStyleSheet("color: white; font-size: 14px; font-weight: bold; background: transparent;");
        debugLabel->resize(120, 120);

        debugWidget->setVisible(false);
        m_characterAnimation = reinterpret_cast<CharacterAnimation*>(debugWidget);
    }

    updateAnimationPosition();
    m_characterAnimation->raise();
    m_characterAnimation->hide();

    qDebug() << "Анимация USB мониторинга инициализирована. Размер:" << m_characterAnimation->size();
}

void Lab5Window::updateAnimationPosition()
{
    if (m_characterAnimation) {
        // Позиционирование в правом нижнем углу как в 4-й лабораторной
        int x = width() - m_characterAnimation->width() - 20;  // 20px отступ справа
        int y = height() - m_characterAnimation->height() - 20; // 20px отступ снизу

        // Проверяем, чтобы не вышло за границы
        if (x < 0) x = 20;
        if (y < 0) y = 20;

        m_characterAnimation->move(x, y);
        m_characterAnimation->raise();

        qDebug() << "Анимация позиционирована: (" << x << "," << y
                 << "), размер:" << m_characterAnimation->size();
    }
}

void Lab5Window::setupSignalHandlers()
{
    connect(m_refreshButton, &QPushButton::clicked, this, &Lab5Window::refreshDeviceList);
    connect(m_ejectButton, &QPushButton::clicked, this, &Lab5Window::handleDeviceEjection);
    connect(m_devicesList, &QListWidget::itemClicked, this, &Lab5Window::showDeviceDetails);
    connect(m_backButton, &QPushButton::clicked, this, &Lab5Window::returnToMainMenu);

    connect(m_usbManager, &USBManager::devicesUpdated, this, &Lab5Window::updateDeviceDisplay);
    connect(m_usbManager, &USBManager::deviceConnected, this, &Lab5Window::onDeviceConnected);
    connect(m_usbManager, &USBManager::deviceDisconnected, this, &Lab5Window::onDeviceDisconnected);
    connect(m_usbManager, &USBManager::ejectionResult, this, &Lab5Window::onEjectionComplete);
}

void Lab5Window::applyCustomStyles()
{
    const QString buttonStyle =
        "QPushButton {"
        "padding: 8px 15px; font-size: 14px; font-weight: bold;"
        "background-color: #D2B48C; color: #8B4513; border-radius: 5px;"
        "border: 2px solid #A0522D;"
        "}"
        "QPushButton:hover { background-color: #BC8F8F; }"
        "QPushButton:pressed { background-color: #A0522D; color: white; }";

    m_refreshButton->setStyleSheet(buttonStyle);
    m_ejectButton->setStyleSheet(buttonStyle);
    m_backButton->setStyleSheet(buttonStyle);

    m_devicesList->setStyleSheet(
        "QListWidget {"
        "background-color: white; border: 2px solid #A0522D; border-radius: 5px;"
        "font-family: 'Segoe UI'; font-size: 12px; padding: 5px;"
        "}"
        "QListWidget::item {"
        "padding: 8px; border-bottom: 1px solid #D2B48C;"
        "}"
        "QListWidget::item:selected {"
        "background-color: #D2B48C; color: #8B4513;"
        "}");

    m_deviceInfoLabel->setStyleSheet(
        "QLabel {"
        "background-color: rgba(210, 180, 140, 0.2);"
        "border: 2px solid #A0522D; border-radius: 5px;"
        "padding: 15px; font-size: 12px; line-height: 1.4;"
        "color: #654321;"
        "}");

    m_statusLabel->setStyleSheet(
        "QLabel {"
        "background-color: rgba(139, 69, 19, 0.1);"
        "border: 1px solid #A0522D; border-radius: 3px;"
        "padding: 5px; font-size: 11px;"
        "color: #8B4513;"
        "}");

    m_devicesGroup->setStyleSheet("QGroupBox { font-weight: bold; color: #8B4513; }");
    m_infoGroup->setStyleSheet("QGroupBox { font-weight: bold; color: #8B4513; }");
}

void Lab5Window::initializeAnimation()
{
    // Инициализация анимации выполнена в initializeCharacterAnimation()
}

void Lab5Window::centerOnScreen()
{
    QScreen *primaryScreen = QGuiApplication::primaryScreen();
    if (!primaryScreen) return;

    QRect screenGeometry = primaryScreen->availableGeometry();
    int x = (screenGeometry.width() - width()) / 2;
    int y = (screenGeometry.height() - height()) / 2;

    x = qMax(0, x);
    y = qMax(0, y);
    x = qMin(screenGeometry.width() - width(), x);
    y = qMin(screenGeometry.height() - height(), y);

    move(x, y);
    qDebug() << "Окно центрировано на экране: (" << x << "," << y << ")";
}

void Lab5Window::resizeEvent(QResizeEvent *event)
{
    QMainWindow::resizeEvent(event);
    qDebug() << "Размер окна изменен на:" << width() << "x" << height();
    updateAnimationPosition();
}

void Lab5Window::showEvent(QShowEvent *event)
{
    QMainWindow::showEvent(event);
    qDebug() << "Окно показано";
    updateAnimationPosition();
}

void Lab5Window::refreshDeviceList()
{
    qDebug() << "Обновление списка устройств...";
    m_usbManager->refreshDevices();
    m_statusLabel->setText("Список устройств обновлен");
}

void Lab5Window::handleDeviceEjection()
{
    QListWidgetItem* currentItem = m_devicesList->currentItem();
    if (!currentItem) {
        QMessageBox::warning(this, "Внимание", "Сначала выберите устройство из списка");
        return;
    }

    QString deviceId = currentItem->data(Qt::UserRole).toString();
    qDebug() << "Попытка извлечения устройства:" << deviceId;
    m_usbManager->ejectDevice(deviceId.toStdWString());
}

void Lab5Window::showDeviceDetails(QListWidgetItem* item)
{
    if (!item) return;

    QString deviceName = item->text();
    m_currentDeviceId = item->data(Qt::UserRole).toString();

    auto devices = m_usbManager->getDevices();
    auto deviceIterator = devices.find(m_currentDeviceId.toStdWString());

    if (deviceIterator != devices.end()) {
        QString deviceInfo = QString("Устройство: %1\n\n"
                                     "Идентификатор производителя: %2\n"
                                     "Идентификатор устройства: %3\n\n"
                                     "Производитель: %4")
                                 .arg(deviceName)
                                 .arg(QString::fromStdWString(deviceIterator->second.vendorId))
                                 .arg(QString::fromStdWString(deviceIterator->second.deviceId))
                                 .arg(QString::fromStdWString(deviceIterator->second.manufacturer));

        m_deviceInfoLabel->setText(deviceInfo);
        qDebug() << "Показана информация об устройстве:" << deviceName;
    }
}

void Lab5Window::updateDeviceDisplay()
{
    refreshDeviceListUI();
}

void Lab5Window::onDeviceConnected(const QString& deviceName)
{
    qDebug() << "=== USB УСТРОЙСТВО ПОДКЛЮЧЕНО ===" << deviceName;
    m_statusLabel->setText("Подключено: " + deviceName);
    startConnectionAnimation();
    refreshDeviceListUI();
}

void Lab5Window::onDeviceDisconnected(const QString& deviceName)
{
    qDebug() << "=== USB УСТРОЙСТВО ОТКЛЮЧЕНО ===" << deviceName;
    if (!m_statusLabel->text().contains("извлечено")) {
        m_statusLabel->setText("Отключено: " + deviceName);
    }
    startDisconnectionAnimation();

    auto devices = m_usbManager->getDevices();
    if (devices.find(m_currentDeviceId.toStdWString()) == devices.end()) {
        m_currentDeviceId.clear();
        m_deviceInfoLabel->setText("Выберите устройство для просмотра информации");
    }

    refreshDeviceListUI();
}

void Lab5Window::onEjectionComplete(const QString& message)
{
    qDebug() << "Результат извлечения:" << message;
    m_statusLabel->setText(message);
    if (message.contains("извлечено")) {
        m_currentDeviceId.clear();
        m_deviceInfoLabel->setText("Выберите устройство для просмотра информации");
        refreshDeviceListUI();
    }
}

void Lab5Window::refreshDeviceListUI()
{
    m_devicesList->clear();

    auto devices = m_usbManager->getDevices();
    int selectedIndex = -1;
    int index = 0;

    for (const auto& devicePair : devices) {
        QString deviceName = QString::fromStdWString(devicePair.second.name);
        QString deviceId = QString::fromStdWString(devicePair.first);

        QListWidgetItem* item = new QListWidgetItem(deviceName);
        item->setData(Qt::UserRole, deviceId);
        m_devicesList->addItem(item);

        if (deviceId == m_currentDeviceId) {
            selectedIndex = index;
        }
        index++;
    }

    if (selectedIndex >= 0) {
        m_devicesList->setCurrentRow(selectedIndex);
        showDeviceDetails(m_devicesList->currentItem());
    } else if (m_devicesList->count() > 0) {
        m_devicesList->setCurrentRow(0);
        showDeviceDetails(m_devicesList->currentItem());
    } else {
        m_deviceInfoLabel->setText("Устройства не обнаружены");
        m_currentDeviceId.clear();
    }

    qDebug() << "Список устройств обновлен. Найдено устройств:" << m_devicesList->count();
}

void Lab5Window::returnToMainMenu()
{
    qDebug() << "Возврат в главное меню";
    emit backToMain();
    close();
}

void Lab5Window::startConnectionAnimation()
{
    qDebug() << ">>> ЗАПУСК АНИМАЦИИ ПОДКЛЮЧЕНИЯ USB";

    if (m_characterAnimation) {
        m_characterAnimation->show();
        m_characterAnimation->raise();

        // Проверяем тип объекта
        CharacterAnimation* animation = qobject_cast<CharacterAnimation*>(m_characterAnimation);
        if (animation) {
            qDebug() << "Запуск CharacterAnimation для подключения USB...";
            qDebug() << " - Размер:" << animation->size();
            qDebug() << " - Позиция:" << animation->pos();
            qDebug() << " - Видимость:" << animation->isVisible();

            animation->startAnimation();
            qDebug() << "Анимация подключения USB ЗАПУЩЕНА";

        } else {
            qDebug() << "Используется ЗАГЛУШКА анимации для подключения";
            QWidget* debugWidget = qobject_cast<QWidget*>(m_characterAnimation);
            if (debugWidget) {
                debugWidget->setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #4CAF50, stop:1 #45a049); border: 2px solid #2E7D32; border-radius: 10px;");
                QLabel* label = debugWidget->findChild<QLabel*>();
                if (label) {
                    label->setText("USB\n✓");
                    label->setStyleSheet("color: white; font-weight: bold; font-size: 14px; background: transparent;");
                }
                debugWidget->show();
            }
        }

        // Скрываем через 3 секунды (немного дольше для USB)
        QTimer::singleShot(3000, this, [this]() {
            qDebug() << "<<< Скрытие анимации подключения USB";
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

void Lab5Window::startDisconnectionAnimation()
{
    qDebug() << ">>> ЗАПУСК АНИМАЦИИ ОТКЛЮЧЕНИЯ USB";

    if (m_characterAnimation) {
        m_characterAnimation->show();
        m_characterAnimation->raise();

        CharacterAnimation* animation = qobject_cast<CharacterAnimation*>(m_characterAnimation);
        if (animation) {
            qDebug() << "Запуск CharacterAnimation для отключения USB...";
            animation->startAnimation();
            qDebug() << "Анимация отключения USB ЗАПУЩЕНА";
        } else {
            qDebug() << "Используется ЗАГЛУШКА анимации для отключения USB";
            QWidget* debugWidget = qobject_cast<QWidget*>(m_characterAnimation);
            if (debugWidget) {
                debugWidget->setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #FF9800, stop:1 #F57C00); border: 2px solid #E65100; border-radius: 10px;");
                QLabel* label = debugWidget->findChild<QLabel*>();
                if (label) {
                    label->setText("USB\n✗");
                    label->setStyleSheet("color: white; font-weight: bold; font-size: 14px; background: transparent;");
                }
                debugWidget->show();
            }
        }

        // Скрываем через 3 секунды
        QTimer::singleShot(3000, this, [this]() {
            qDebug() << "<<< Скрытие анимации отключения USB";
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
