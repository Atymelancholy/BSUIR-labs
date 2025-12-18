#include "maininterface.h"
#include <QApplication>

MainInterface::MainInterface(QWidget *parent)
    : QMainWindow(parent)
    , contentArea(0)
    , homeScreen(0)
    , deviceScanner(0)
    , nextLabScreen(0)
{
    setWindowTitle("Academic Laboratory Manager");
    setMinimumSize(800, 600);
    showMaximized();

    initializeComponents();
    setupVisualStyle();
}

MainInterface::~MainInterface()
{
}

void MainInterface::initializeComponents()
{
    contentArea = new QStackedWidget(this);
    setCentralWidget(contentArea);

    createHomeScreen();
    createNextLabScreen();

    //deviceScanner = new DeviceScanner();

    contentArea->addWidget(homeScreen);
   // contentArea->addWidget(deviceScanner);
    contentArea->addWidget(nextLabScreen);
    contentArea->setCurrentWidget(homeScreen);
}

void MainInterface::createHomeScreen()
{
    homeScreen = new QWidget();
    QVBoxLayout *mainLayout = new QVBoxLayout(homeScreen);
    mainLayout->setContentsMargins(50, 100, 50, 100);
    mainLayout->setSpacing(40);

    QLabel *headerText = new QLabel("Academic Laboratory Projects");
    headerText->setObjectName("mainHeader");
    headerText->setAlignment(Qt::AlignCenter);
    mainLayout->addWidget(headerText);

    mainLayout->addStretch();

    QVBoxLayout *actionButtonsLayout = new QVBoxLayout();
    actionButtonsLayout->setSpacing(20);
    actionButtonsLayout->setAlignment(Qt::AlignCenter);

    QPushButton *scanButton = new QPushButton("Project #2\nHardware Device Scanner");
    scanButton->setObjectName("actionButton");
    scanButton->setFixedSize(400, 100);
    connect(scanButton, &QPushButton::clicked, this, &MainInterface::displayDeviceScanner);
    actionButtonsLayout->addWidget(scanButton);

    QPushButton *nextProjectButton = new QPushButton("Project #3\nComing Soon");
    nextProjectButton->setObjectName("actionButton");
    nextProjectButton->setFixedSize(400, 100);
    connect(nextProjectButton, &QPushButton::clicked, this, &MainInterface::displayNextLab);
    actionButtonsLayout->addWidget(nextProjectButton);

    mainLayout->addLayout(actionButtonsLayout);
    mainLayout->addStretch();

    QHBoxLayout *footerLayout = new QHBoxLayout();
    footerLayout->addStretch();

    QPushButton *closeAppButton = new QPushButton("Close");
    closeAppButton->setObjectName("closeButton");
    closeAppButton->setFixedSize(150, 50);
    connect(closeAppButton, &QPushButton::clicked, qApp, &QApplication::quit);

    footerLayout->addWidget(closeAppButton);
    mainLayout->addLayout(footerLayout);
}

void MainInterface::createNextLabScreen()
{
    nextLabScreen = new QWidget();
    QVBoxLayout *nextLabLayout = new QVBoxLayout(nextLabScreen);
    nextLabLayout->setContentsMargins(50, 50, 50, 50);

    QLabel *nextLabLabel = new QLabel("Project #3\n\n??? In Development Phase ???");
    nextLabLabel->setObjectName("projectLabel");
    nextLabLabel->setAlignment(Qt::AlignCenter);
    nextLabLayout->addWidget(nextLabLabel);
}

void MainInterface::setupVisualStyle()
{
    setStyleSheet(
        "QMainWindow {"
        "   background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #F8F4E6, stop:1 #E8DCC8);"
        "}"
        ""
        "#mainHeader {"
        "   color: #5D4037;"
        "   font-size: 42px;"
        "   font-weight: bold;"
        "   background: rgba(255, 251, 240, 200);"
        "   padding: 25px 45px;"
        "   border-radius: 18px;"
        "   border: 2px solid #BCAA9A;"
        "}"
        ""
        "#actionButton {"
        "   background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #6D4C41, stop:1 #4E342E);"
        "   color: #FBF7F0;"
        "   font-size: 16px;"
        "   font-weight: bold;"
        "   border: 2px solid #8D6E63;"
        "   border-radius: 12px;"
        "   padding: 18px;"
        "}"
        ""
        "#actionButton:hover {"
        "   background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #8D6E63, stop:1 #6D4C41);"
        "   color: #FFF8E1;"
        "   border: 2px solid #6D4C41;"
        "}"
        ""
        "#actionButton:pressed {"
        "   background: #4E342E;"
        "}"
        ""
        "#closeButton {"
        "   background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #C62828, stop:1 #8E0000);"
        "   color: #FBF7F0;"
        "   font-weight: bold;"
        "   border: 2px solid #D32F2F;"
        "   padding: 10px 20px;"
        "   border-radius: 8px;"
        "   font-size: 13px;"
        "}"
        ""
        "#closeButton:hover {"
        "   background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #D32F2F, stop:1 #B71C1C);"
        "   color: #FFEBEE;"
        "   border: 2px solid #C62828;"
        "}"
        ""
        "#projectLabel {"
        "   color: #5D4037;"
        "   font-size: 32px;"
        "   font-weight: bold;"
        "   background: rgba(255, 251, 240, 200);"
        "   padding: 40px;"
        "   border-radius: 18px;"
        "   border: 2px solid #BCAA9A;"
        "}"
    );
}

void MainInterface::displayDeviceScanner()
{
    contentArea->setCurrentWidget(deviceScanner);
}

void MainInterface::displayNextLab()
{
    contentArea->setCurrentWidget(nextLabScreen);
}

void MainInterface::returnToHome()
{
    contentArea->setCurrentWidget(homeScreen);
}
