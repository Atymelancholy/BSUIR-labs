#include "mainwindow.h"
#include "ui_mainwindow.h"
#include "lab1window.h"

#include <QPropertyAnimation>
#include <QEasingCurve>
#include <QGraphicsOpacityEffect>
#include <QTimer>
#include <QLabel>
#include <QPixmap>
#include <QDebug>
#include <QVBoxLayout>
#include <QPushButton>

MainWindow::MainWindow(QWidget *parent)
    : QMainWindow(parent)
    , ui(new Ui::MainWindow)
    , m_lab1Window(nullptr)
    , characterImageLabel(nullptr)
    , titleLabel(nullptr)
    , pigImageLabel(nullptr)
    , pigButton(nullptr)
{
    ui->setupUi(this);

    setupBackground();
    setupUI();
    positionElements();
}

MainWindow::~MainWindow()
{
    delete m_lab1Window;
    delete characterImageLabel;
    delete pigImageLabel;
    delete pigButton;
    delete ui;
}

void MainWindow::setupBackground()
{
    // Устанавливаем бежевый фон
    setStyleSheet("QMainWindow { background-color: #F5F5DC; }");
    qDebug() << "Установлен бежевый фон";
}

void MainWindow::setupUI()
{
    QWidget *centralWidget = new QWidget(this);
    setCentralWidget(centralWidget);

    // Заголовок
    titleLabel = new QLabel("Лабораторные работы по ИиУВМ", centralWidget);
    titleLabel->setStyleSheet("font-size: 28px; font-weight: bold; color: #8B4513; "
                              "text-shadow: 1px 1px 2px rgba(255,255,255,0.7);");
    titleLabel->setAlignment(Qt::AlignCenter);

    // Картинка свинки (заменяет все ступеньки)
    pigImageLabel = new QLabel(centralWidget);
    QPixmap pigPixmap(":/resources/images/pngwing.com.png");
    if (!pigPixmap.isNull()) {
        // Масштабируем картинку под нужный размер
        pigImageLabel->setPixmap(pigPixmap.scaled(300, 250, Qt::KeepAspectRatio, Qt::SmoothTransformation));
        pigImageLabel->setFixedSize(pigPixmap.scaled(300, 250, Qt::KeepAspectRatio, Qt::SmoothTransformation).size());
    } else {
        qDebug() << "Не удалось загрузить картинку pngwing.com.png";
        pigImageLabel->setStyleSheet("background-color: pink; border: 2px solid darkred;");
        pigImageLabel->setText("Свинка\nnot found");
        pigImageLabel->setAlignment(Qt::AlignCenter);
        pigImageLabel->setFixedSize(300, 250);
    }
    pigImageLabel->setAttribute(Qt::WA_TransparentForMouseEvents);

    // Кнопка поверх картинки свинки
    pigButton = new QPushButton(centralWidget);
    pigButton->setFixedSize(pigImageLabel->size());
    pigButton->setStyleSheet(
        "QPushButton {"
        "background-color: transparent;"
        "border: none;"
        "}"
        "QPushButton:hover {"
        "background-color: rgba(255,255,255,0.1);"
        "border: 2px dashed #8B4513;"
        "border-radius: 10px;"
        "}"
        );
    connect(pigButton, &QPushButton::clicked, this, &MainWindow::onPigButtonClicked);

    // Статичная картинка m.png
    characterImageLabel = new QLabel(centralWidget);
    characterImageLabel->setFixedSize(150, 150);
    QPixmap characterPixmap(":/resources/images/m.png");
    if (!characterPixmap.isNull()) {
        characterImageLabel->setPixmap(characterPixmap.scaled(150, 150, Qt::KeepAspectRatio, Qt::SmoothTransformation));
    } else {
        qDebug() << "Не удалось загрузить картинку m.png";
        characterImageLabel->setStyleSheet("background-color: gray; border: 2px solid black;");
        characterImageLabel->setText("m.png\nnot found");
        characterImageLabel->setAlignment(Qt::AlignCenter);
    }
    characterImageLabel->setAttribute(Qt::WA_TransparentForMouseEvents);

    // Эффект плавного появления для кнопки
    auto *effect = new QGraphicsOpacityEffect(pigButton);
    pigButton->setGraphicsEffect(effect);
    effect->setOpacity(0);

    auto *anim = new QPropertyAnimation(effect, "opacity");
    anim->setDuration(1000);
    anim->setStartValue(0);
    anim->setEndValue(1);
    anim->setEasingCurve(QEasingCurve::InOutQuad);
    anim->start();
}

void MainWindow::onPigButtonClicked()
{
    qDebug() << "Свинка нажата! Открываем лабораторную работу...";
    showLab1Window();
}

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

void MainWindow::backToMain()
{
    if (m_lab1Window) m_lab1Window->hide();
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

    // Позиционируем заголовок
    if (titleLabel) {
        titleLabel->setGeometry(0, h/4 - 50, w, 50);
    }

    // Позиционируем картинку свинки по центру
    if (pigImageLabel) {
        pigImageLabel->move(w/2 - pigImageLabel->width()/2, h/2 - pigImageLabel->height()/2);
    }

    // Позиционируем кнопку поверх картинки свинки
    if (pigButton && pigImageLabel) {
        pigButton->move(pigImageLabel->pos());
    }

    // Позиционируем статичную картинку персонажа внизу
    if (characterImageLabel) {
        characterImageLabel->move(w/2 - 75, h - 200);
    }

    // Поднимаем все элементы на верхний уровень
    if (titleLabel) titleLabel->raise();
    if (pigButton) pigButton->raise();
    if (characterImageLabel) characterImageLabel->raise();
}
