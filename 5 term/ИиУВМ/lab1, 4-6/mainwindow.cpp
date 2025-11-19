#include "mainwindow.h"
#include "ui_mainwindow.h"
#include "lab1window.h"
#include "lab4window.h"
#include "lab5window.h"
#include "lab6window.h"

#include <QPropertyAnimation>
#include <QEasingCurve>
#include <QGraphicsOpacityEffect>
#include <QTimer>
#include <QLabel>
#include <QPixmap>
#include <QDebug>
#include <QVBoxLayout>
#include <QPushButton>
#include <QMessageBox>

MainWindow::MainWindow(QWidget *parent)
    : QMainWindow(parent)
    , ui(new Ui::MainWindow)
    , m_lab1Window(nullptr)
    , m_lab4Window(nullptr)
    , m_lab5Window(nullptr)
    , m_lab6Window(nullptr)  // В списке инициализации
    , characterImageLabel(nullptr)
    , titleLabel(nullptr)
{
    ui->setupUi(this);

    for (int i = 0; i < 6; ++i) {
        pigImageLabels[i] = nullptr;
        pigButtons[i] = nullptr;
    }

    setupBackground();
    setupUI();
    positionElements();
}

MainWindow::~MainWindow()
{
    delete m_lab1Window;
    delete m_lab4Window;
    delete m_lab5Window;
    delete m_lab6Window;
    delete characterImageLabel;
    delete titleLabel;

    for (int i = 0; i < 6; ++i) {
        delete pigImageLabels[i];
        delete pigButtons[i];
    }
    delete ui;
}

void MainWindow::setupBackground()
{
    setStyleSheet("QMainWindow { background-color: #F5F5DC; }");
}

void MainWindow::setupUI()
{
    QWidget *centralWidget = new QWidget(this);
    setCentralWidget(centralWidget);

    titleLabel = new QLabel("Лабораторные работы по ИиУВМ", centralWidget);
    titleLabel->setStyleSheet("font-size: 28px; font-weight: bold; color: #8B4513; text-shadow: 1px 1px 2px rgba(255,255,255,0.7);");
    titleLabel->setAlignment(Qt::AlignCenter);

    QString tooltips[6] = {
        "Лабораторная работа 1 - Управление питанием",
        "Лабораторная работа 2 - В разработке",
        "Лабораторная работа 3 - В разработке",
        "Лабораторная работа 4 - Работа с камерой",
        "Лабораторная работа 5 - Мониторинг USB устройств",
        "Лабораторная работа 6 - Bluetooth File Transfer"
    };

    for (int i = 0; i < 6; ++i) {
        pigImageLabels[i] = new QLabel(centralWidget);
        QPixmap pigPixmap(":/resources/images/pngwing.com.png");
        if (!pigPixmap.isNull()) {
            pigImageLabels[i]->setPixmap(pigPixmap.scaled(120, 100, Qt::KeepAspectRatio, Qt::SmoothTransformation));
            pigImageLabels[i]->setFixedSize(120, 100);
        } else {
            QString color;
            if (i == 0) color = "#32CD32";
            else if (i == 3) color = "#32CD32";
            else if (i == 4) color = "#4169E1";
            else if (i == 5) color = "#9370DB";
            else color = "#A9A9A9";

            pigImageLabels[i]->setStyleSheet(QString("background-color: %1; border: 2px solid darkred; border-radius: 10px; color: white; font-weight: bold;").arg(color));
            pigImageLabels[i]->setText(QString("Лаб %1").arg(i+1));
            pigImageLabels[i]->setAlignment(Qt::AlignCenter);
            pigImageLabels[i]->setFixedSize(120, 100);
        }
        pigImageLabels[i]->setAttribute(Qt::WA_TransparentForMouseEvents);

        pigButtons[i] = new QPushButton(centralWidget);
        pigButtons[i]->setFixedSize(120, 100);
        pigButtons[i]->setToolTip(tooltips[i]);
        pigButtons[i]->setStyleSheet(
            "QPushButton {"
            "background-color: transparent;"
            "border: 2px solid transparent;"
            "border-radius: 15px;"
            "}"
            "QPushButton:hover {"
            "background-color: rgba(139, 69, 19, 0.1);"
            "border: 2px solid #8B4513;"
            "}"
            "QPushButton:pressed {"
            "background-color: rgba(139, 69, 19, 0.2);"
            "}"
            );

        switch (i) {
        case 0: connect(pigButtons[i], &QPushButton::clicked, this, &MainWindow::onPigButton1Clicked); break;
        case 1: connect(pigButtons[i], &QPushButton::clicked, this, &MainWindow::onPigButton2Clicked); break;
        case 2: connect(pigButtons[i], &QPushButton::clicked, this, &MainWindow::onPigButton3Clicked); break;
        case 3: connect(pigButtons[i], &QPushButton::clicked, this, &MainWindow::onPigButton4Clicked); break;
        case 4: connect(pigButtons[i], &QPushButton::clicked, this, &MainWindow::onPigButton5Clicked); break;
        case 5: connect(pigButtons[i], &QPushButton::clicked, this, &MainWindow::onPigButton6Clicked); break;
        }

        QGraphicsOpacityEffect *effect = new QGraphicsOpacityEffect(pigButtons[i]);
        pigButtons[i]->setGraphicsEffect(effect);
        effect->setOpacity(0);

        QPropertyAnimation *anim = new QPropertyAnimation(effect, "opacity");
        anim->setDuration(1000);
        anim->setStartValue(0);
        anim->setEndValue(1);
        anim->setEasingCurve(QEasingCurve::InOutQuad);
        anim->start();
    }

    characterImageLabel = new QLabel(centralWidget);
    characterImageLabel->setFixedSize(150, 150);
    QPixmap characterPixmap(":/resources/images/m.png");
    if (!characterPixmap.isNull()) {
        characterImageLabel->setPixmap(characterPixmap.scaled(150, 150, Qt::KeepAspectRatio, Qt::SmoothTransformation));
    } else {
        characterImageLabel->setStyleSheet("background-color: gray; border: 2px solid black; border-radius: 10px;");
        characterImageLabel->setText("m.png\nnot found");
        characterImageLabel->setAlignment(Qt::AlignCenter);
    }
    characterImageLabel->setAttribute(Qt::WA_TransparentForMouseEvents);
}

void MainWindow::onPigButton1Clicked() { showLab1Window(); }
void MainWindow::onPigButton2Clicked() { showLab2Window(); }
void MainWindow::onPigButton3Clicked() { showLab3Window(); }
void MainWindow::onPigButton4Clicked() { showLab4Window(); }
void MainWindow::onPigButton5Clicked() { showLab5Window(); }
void MainWindow::onPigButton6Clicked() { showLab6Window(); }

void MainWindow::showLab1Window()
{
    if (!m_lab1Window) {
        m_lab1Window = new Lab1Window(this);
        connect(m_lab1Window, &Lab1Window::backToMain, this, &MainWindow::backToMain);
    }
    m_lab1Window->show();
    m_lab1Window->raise();
    m_lab1Window->activateWindow();
}

void MainWindow::showLab4Window()
{
    if (!m_lab4Window) {
        m_lab4Window = new Lab4Window(this);
        connect(m_lab4Window, &Lab4Window::backToMain, this, &MainWindow::backToMain);
    }
    m_lab4Window->show();
    m_lab4Window->raise();
    m_lab4Window->activateWindow();
}

void MainWindow::showLab5Window()
{
    if (!m_lab5Window) {
        m_lab5Window = new Lab5Window(this);
        connect(m_lab5Window, &Lab5Window::backToMain, this, &MainWindow::backToMain);
    }
    m_lab5Window->show();
    m_lab5Window->raise();
    m_lab5Window->activateWindow();
}



void MainWindow::showLab6Window()
{
    if (!m_lab6Window) {
        m_lab6Window = new Lab6Window(this);
        connect(m_lab6Window, &Lab6Window::backToMain, this, &MainWindow::backToMain);
    }
    m_lab6Window->show();
    m_lab6Window->raise();
    m_lab6Window->activateWindow();
}
void MainWindow::showLab2Window()
{
    QMessageBox::information(this, "В разработке", "Лабораторная работа 2 находится в разработке.\n\nЧтобы просмотреть работоспособность, откройте Virtual Box");
}

void MainWindow::showLab3Window()
{
    QMessageBox::information(this, "В разработке", "Лабораторная работа 3 находится в разработке.\n\nЧтобы просмотреть работоспособность, откройте Virtual Box");
}

void MainWindow::backToMain()
{
    if (m_lab1Window) m_lab1Window->hide();
    if (m_lab4Window) m_lab4Window->hide();
    if (m_lab5Window) m_lab5Window->hide();
    if (m_lab6Window) m_lab6Window->hide();
}

void MainWindow::resizeEvent(QResizeEvent *event)
{
    QMainWindow::resizeEvent(event);
    positionElements();
}

void MainWindow::positionElements()
{
    int w = width();
    int h = height();

    if (titleLabel) {
        titleLabel->setGeometry(0, 50, w, 50);
    }

    int pigWidth = 120;
    int pigHeight = 100;
    int horizontalSpacing = (w - 3 * pigWidth) / 4;
    int verticalSpacing = 40;

    int totalGridHeight = 2 * pigHeight + verticalSpacing;
    int startY = h/2 - totalGridHeight/2;

    for (int row = 0; row < 2; ++row) {
        for (int col = 0; col < 3; ++col) {
            int index = row * 3 + col;
            if (index >= 6) break;

            int x = horizontalSpacing + col * (pigWidth + horizontalSpacing);
            int y = startY + row * (pigHeight + verticalSpacing);

            if (pigImageLabels[index]) {
                pigImageLabels[index]->move(x, y);
            }
            if (pigButtons[index]) {
                pigButtons[index]->move(x, y);
            }
        }
    }

    if (characterImageLabel) {
        characterImageLabel->move(w/2 - 75, h - 200);
    }

    if (titleLabel) titleLabel->raise();
    for (int i = 0; i < 6; ++i) {
        if (pigButtons[i]) pigButtons[i]->raise();
        if (pigImageLabels[i]) pigImageLabels[i]->raise();
    }
    if (characterImageLabel) characterImageLabel->raise();
}
