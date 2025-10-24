#include "lab1window.h"
#include <QVBoxLayout>
#include <QHBoxLayout>
#include <QPushButton>
#include <QLabel>
#include <QDebug>
#include <QMessageBox>
#include <QGroupBox>
#include <QFrame>
#include <QTimer>
#include "battery.h"
#include "characteranimation.h"

// Функция для форматирования времени из секунд в читаемый формат
QString formatTime(int seconds) {
    if (seconds <= 0) {
        return "unknown";
    }

    int hours = seconds / 3600;
    int minutes = (seconds % 3600) / 60;

    if (hours > 0) {
        return QString("%1ч %2мин").arg(hours).arg(minutes);
    } else {
        return QString("%1мин").arg(minutes);
    }
}

Lab1Window::Lab1Window(QWidget *parent) :
    QMainWindow(parent),
    backgroundLabel(nullptr),
    batteryInfoLabel(nullptr),
    m_characterAnimation(nullptr),
    m_staticImageLabel(nullptr)
{
    setWindowTitle("Лабораторная работа 1 - Управление питанием");
    resize(1000, 700);

    // Устанавливаем бежевый фон
    setStyleSheet("QMainWindow { background-color: #F5F5DC; }");

    setupUI();

    // Создаем анимацию персонажа
    m_characterAnimation = new CharacterAnimation(this);
    m_characterAnimation->setFixedSize(150, 150);
    m_characterAnimation->setBackgroundColor(Qt::transparent);
    m_characterAnimation->loadSpriteSheet(":/resources/images/Untitled-5.png", 147, 102);
    m_characterAnimation->setAnimationSpeed(100);
    m_characterAnimation->hide();

    // Создаем статичную картинку с правильным соотношением сторон
    m_staticImageLabel = new QLabel(this);
    m_staticImageLabel->setFixedSize(250, 150);
    m_staticImageLabel->setAlignment(Qt::AlignCenter);
    m_staticImageLabel->setScaledContents(true);

    // Загружаем статичное изображение
    QPixmap pmPixmap(":/resources/images/pm.png");
    if (!pmPixmap.isNull()) {
        m_staticImageLabel->setPixmap(pmPixmap.scaled(200, 150, Qt::KeepAspectRatio, Qt::SmoothTransformation));
    } else {
        m_staticImageLabel->setText("pm.png");
        m_staticImageLabel->setStyleSheet("color: gray; font-size: 12px;");
    }
    m_staticImageLabel->show();

    updateAnimationPosition();

    QTimer *timer = new QTimer(this);
    connect(timer, &QTimer::timeout, this, &Lab1Window::updateBatteryInfo);
    timer->start(2000);
}

Lab1Window::~Lab1Window()
{
    if (m_characterAnimation) delete m_characterAnimation;
    if (m_staticImageLabel) delete m_staticImageLabel;
}

void Lab1Window::updateAnimationPosition()
{
    int x = (width() - 200) / 2;
    int y = height() - 150 - 20;

    if (m_characterAnimation) {
        m_characterAnimation->move(x, y);
        m_characterAnimation->raise();
    }

    if (m_staticImageLabel) {
        m_staticImageLabel->move(x, y);
        m_staticImageLabel->raise();
    }
}

void Lab1Window::setupUI()
{
    QWidget *centralWidget = new QWidget(this);
    QVBoxLayout *mainLayout = new QVBoxLayout(centralWidget);
    mainLayout->setContentsMargins(20, 20, 20, 100);
    mainLayout->setSpacing(15);

    // Заголовок
    QLabel *titleLabel = new QLabel("Управление питанием", centralWidget);
    titleLabel->setStyleSheet("font-size: 24px; font-weight: bold; color: #8B4513;");
    titleLabel->setAlignment(Qt::AlignCenter);

    // Основной контейнер без рамки
    QWidget *mainContainer = new QWidget(centralWidget);
    mainContainer->setStyleSheet("background: transparent;");

    QHBoxLayout *containerLayout = new QHBoxLayout(mainContainer);
    containerLayout->setContentsMargins(0, 0, 0, 0);
    containerLayout->setSpacing(40);

    // Левая часть - информация о батарее (без рамки)
    QWidget *infoWidget = new QWidget(mainContainer);
    infoWidget->setStyleSheet("background: transparent;");
    QVBoxLayout *infoLayout = new QVBoxLayout(infoWidget);
    infoLayout->setContentsMargins(0, 0, 0, 0);
    infoLayout->setSpacing(15);

    QLabel *infoTitle = new QLabel("Информация о батарее", infoWidget);
    infoTitle->setStyleSheet("font-size: 18px; font-weight: bold; color: #8B4513;");

    batteryInfoLabel = new QLabel(infoWidget);
    batteryInfoLabel->setStyleSheet(
        "font-size: 14px; color: #654321; line-height: 1.6;"
        "background-color: rgba(210, 180, 140, 0.2);"
        "border-radius: 8px; padding: 15px;"
        );
    batteryInfoLabel->setWordWrap(true);
    batteryInfoLabel->setMinimumWidth(450);

    infoLayout->addWidget(infoTitle);
    infoLayout->addWidget(batteryInfoLabel);
    infoLayout->addStretch();

    // Правая часть - управление питанием (без рамки)
    QWidget *controlWidget = new QWidget(mainContainer);
    controlWidget->setStyleSheet("background: transparent;");
    QVBoxLayout *controlLayout = new QVBoxLayout(controlWidget);
    controlLayout->setContentsMargins(0, 0, 0, 0);
    controlLayout->setSpacing(20);

    QLabel *controlTitle = new QLabel("Управление", controlWidget);
    controlTitle->setStyleSheet("font-size: 18px; font-weight: bold; color: #8B4513;");

    // Кнопка спящего режима
    QPushButton *sleepButton = new QPushButton("Спящий режим", controlWidget);
    sleepButton->setStyleSheet(
        "QPushButton {"
        "padding: 15px 25px; font-size: 14px; font-weight: bold;"
        "background-color: #D2B48C; color: #8B4513; border-radius: 10px;"
        "border: 2px solid #A0522D; min-width: 200px;"
        "}"
        "QPushButton:hover { background-color: #BC8F8F; }"
        "QPushButton:pressed { background-color: #A0522D; color: white; }"
        );
    sleepButton->setFixedHeight(60);

    // Кнопка гибернации
    QPushButton *hibernateButton = new QPushButton("Гибернация", controlWidget);
    hibernateButton->setStyleSheet(
        "QPushButton {"
        "padding: 15px 25px; font-size: 14px; font-weight: bold;"
        "background-color: #DEB887; color: #8B4513; border-radius: 10px;"
        "border: 2px solid #A0522D; min-width: 200px;"
        "}"
        "QPushButton:hover { background-color: #CD853F; }"
        "QPushButton:pressed { background-color: #A0522D; color: white; }"
        );
    hibernateButton->setFixedHeight(60);

    controlLayout->addWidget(controlTitle);
    controlLayout->addSpacing(10);
    controlLayout->addWidget(sleepButton);
    controlLayout->addWidget(hibernateButton);
    controlLayout->addStretch();

    // Добавляем обе части в основной контейнер
    containerLayout->addWidget(infoWidget);
    containerLayout->addWidget(controlWidget);

    // Подключаем сигналы
    connect(sleepButton, &QPushButton::clicked, this, &Lab1Window::onSleepClicked);
    connect(hibernateButton, &QPushButton::clicked, this, &Lab1Window::onHibernateClicked);

    // Добавляем все в главный layout
    mainLayout->addWidget(titleLabel);
    mainLayout->addWidget(mainContainer);
    mainLayout->addStretch();

    setCentralWidget(centralWidget);
    updateBatteryInfo();
}

void Lab1Window::updateBatteryInfo()
{
    Battery battery;
    BatteryInfo info = battery.getBatteryInfo();

    QString batteryText = QString(
                              "Состояние: %1\n\n"
                              "Питание: %2\n\n"
                              "Уровень заряда: %3%\n\n"
                              "Оставшееся время: %4\n\n"
                              "Тип аккумулятора: %5\n\n"
                              "Энергосбережение: %6"
                              ).arg(QString::fromStdString(info.stateOfCharge))
                              .arg(QString::fromStdString(info.powerSupply))
                              .arg(info.percentage)
                              .arg(formatTime(info.lifeTime))
                              .arg(QString::fromStdString(info.chemistry))
                              .arg(QString::fromStdString(info.savingMode));

    if (batteryInfoLabel) {
        batteryInfoLabel->setText(batteryText);
    }

    if (m_characterAnimation && m_staticImageLabel) {
        if (info.stateOfCharge == "charging") {
            m_characterAnimation->show();
            m_characterAnimation->startAnimation();
            m_characterAnimation->raise();
            m_staticImageLabel->hide();
        } else {
            m_staticImageLabel->show();
            m_staticImageLabel->raise();
            m_characterAnimation->hide();
            m_characterAnimation->stopAnimation();
        }
    }
}

void Lab1Window::resizeEvent(QResizeEvent *event)
{
    QMainWindow::resizeEvent(event);
    updateAnimationPosition();
}

void Lab1Window::showEvent(QShowEvent *event)
{
    QMainWindow::showEvent(event);
    updateBatteryInfo();
    updateAnimationPosition();
}

void Lab1Window::onSleepClicked()
{
    if (QMessageBox::question(this, "Подтверждение",
                              "Перевести компьютер в спящий режим?",
                              QMessageBox::Yes | QMessageBox::No) == QMessageBox::Yes) {
        system("rundll32.exe powrprof.dll,SetSuspendState 0,0,0");
    }
}

void Lab1Window::onHibernateClicked()
{
    if (QMessageBox::question(this, "Подтверждение",
                              "Перевести компьютер в режим гибернации?",
                              QMessageBox::Yes | QMessageBox::No) == QMessageBox::Yes) {
        system("rundll32.exe powrprof.dll,SetSuspendState 1,0,0");
    }
}

void Lab1Window::onBackClicked()
{
    emit backToMain();
    close();
}
