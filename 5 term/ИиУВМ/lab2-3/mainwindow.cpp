#include "mainwindow.h"
#include "pciwindow.h"
#include "atawindow.h"
#include <QApplication>
#include <QVBoxLayout>
#include <QHBoxLayout>
#include <QLabel>
#include <QPushButton>
#include <QStackedWidget>

MainWindow::MainWindow(QWidget *parent)
    : QMainWindow(parent)
    , stackedWidget(0)
    , homeScreen(0)
    , pciScreen(0)
    , ataScreen(0)
{
    setWindowTitle("Academic Laboratory Manager");
    setMinimumSize(800, 600);
    setupUI();
    setupStyles();
}

MainWindow::~MainWindow() {}

void MainWindow::setupUI()
{
    stackedWidget = new QStackedWidget(this);
    setCentralWidget(stackedWidget);

    createHomeScreen();
    createPCIScreen();
    createATAScreen();

    stackedWidget->addWidget(homeScreen);
    stackedWidget->addWidget(pciScreen);
    stackedWidget->addWidget(ataScreen);

    stackedWidget->setCurrentWidget(homeScreen);
}

void MainWindow::setupStyles()
{
    setStyleSheet(
        "QMainWindow { "
        "   background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #FAF6ED, stop:1 #EDE3D2); "
        "} "
        "QPushButton { "
        "   background-color: #7B5E57; "
        "   color: white; "
        "   font-size: 16px; "
        "   font-weight: bold; "
        "   padding: 12px; "
        "   border: none; "
        "   border-radius: 12px; "
        "   min-width: 250px; "
        "} "
        "QPushButton:hover { background-color: #8D6E63; } "
        "QPushButton:pressed { background-color: #5D4037; } "
        "QLabel { "
        "   color: #4E342E; "
        "} "
        "QLabel#titleLabel { "
        "   font-size: 32px; "
        "   font-weight: bold; "
        "   text-align: center; "
        "} "
        "QLabel#subtitleLabel { "
        "   color: #6D4C41; "
        "   font-size: 14px; "
        "   font-style: italic; "
        "   text-align: center; "
        "} "
    );
}

void MainWindow::createHomeScreen()
{
    homeScreen = new QWidget();
    QVBoxLayout *layout = new QVBoxLayout(homeScreen);
    layout->setContentsMargins(50, 80, 50, 80);
    layout->setSpacing(40);

    QLabel *title = new QLabel("Academic Laboratory Projects");
    title->setObjectName("titleLabel");
    title->setAlignment(Qt::AlignCenter);
    layout->addWidget(title);

    QLabel *subtitle = new QLabel("Select a laboratory to launch:");
    subtitle->setObjectName("subtitleLabel");
    subtitle->setAlignment(Qt::AlignCenter);
    layout->addWidget(subtitle);

    layout->addStretch();

    QPushButton *pciButton = new QPushButton("Laboratory #2\nPCI Devices Scanner");
    pciButton->setToolTip("Scan PCI devices on your system");
    connect(pciButton, SIGNAL(clicked()), this, SLOT(showPCIScanner()));
    layout->addWidget(pciButton, 0, Qt::AlignCenter);

    QPushButton *ataButton = new QPushButton("Laboratory #3\nATA/IDE HDD/SSD Scanner");
    ataButton->setToolTip("Scan ATA/IDE hard drives and solid state drives");
    connect(ataButton, SIGNAL(clicked()), this, SLOT(showATAScanner()));
    layout->addWidget(ataButton, 0, Qt::AlignCenter);

    layout->addStretch();
}

void MainWindow::createPCIScreen()
{
    pciScreen = new PCIWindow();
    connect(pciScreen, SIGNAL(backToMainMenu()), this, SLOT(returnToHome()));
}

void MainWindow::createATAScreen()
{
    ataScreen = new ATAWindow();
    connect(ataScreen, SIGNAL(backToMainMenu()), this, SLOT(returnToHome()));
}

void MainWindow::showPCIScanner()
{
    if (pciScreen) {
        stackedWidget->setCurrentWidget(pciScreen);
    }
}

void MainWindow::showATAScanner()
{
    if (ataScreen) {
        stackedWidget->setCurrentWidget(ataScreen);
    }
}

void MainWindow::returnToHome()
{
    if (homeScreen) {
        stackedWidget->setCurrentWidget(homeScreen);
    }
}
