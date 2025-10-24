#include "stepbutton.h"
#include <QPainter>
#include <QEnterEvent>
#include <QMouseEvent>
#include <QDebug>

StepButton::StepButton(QWidget *parent)
    : QWidget(parent)
    , m_state(StateFixed)
    , m_stepNumber(1)
    , m_isPressed(false)
    , m_isHovered(false)
    , m_currentScale(1.0)
{
    loadStepImages();
    setupAnimations();
    setFixedSize(100, 100);
    setCursor(Qt::PointingHandCursor);
}

StepButton::StepButton(StepState state, int number, QWidget *parent)
    : QWidget(parent)
    , m_state(state)
    , m_stepNumber(number)
    , m_isPressed(false)
    , m_isHovered(false)
    , m_currentScale(1.0)
{
    loadStepImages();
    setupAnimations();
    setFixedSize(100, 100);
    setCursor(Qt::PointingHandCursor);

    setToolTip(m_state == StateFixed ?
                   QString("Лаб. работа %1 - Доступна").arg(number) :
                   QString("Лаб. работа %1 - В разработке").arg(number));
}

void StepButton::loadStepImages()
{
    // Загружаем PNG изображения ступенек
    m_fixedStepPixmap.load(":/resources/images/step.png");
    m_brokenStepPixmap.load("://resources/images/BROKE copy.png");

    // Если изображения не загрузились, создаем цветные заглушки
    if (m_fixedStepPixmap.isNull()) {
        m_fixedStepPixmap = QPixmap(80, 80);
        m_fixedStepPixmap.fill(Qt::green);
        QPainter painter(&m_fixedStepPixmap);
        painter.setPen(Qt::white);
        painter.drawText(m_fixedStepPixmap.rect(), Qt::AlignCenter, "Fixed");
    }

    if (m_brokenStepPixmap.isNull()) {
        m_brokenStepPixmap = QPixmap(80, 80);
        m_brokenStepPixmap.fill(Qt::red);
        QPainter painter(&m_brokenStepPixmap);
        painter.setPen(Qt::white);
        painter.drawText(m_brokenStepPixmap.rect(), Qt::AlignCenter, "Broken");
    }
}

void StepButton::setupAnimations()
{
    // Анимация при наведении
    m_hoverAnimation = new QPropertyAnimation(this, "currentScale");
    m_hoverAnimation->setDuration(200);
    m_hoverAnimation->setEasingCurve(QEasingCurve::OutBack);

    // Анимация при клике
    m_clickAnimation = new QPropertyAnimation(this, "currentScale");
    m_clickAnimation->setDuration(100);
    m_clickAnimation->setEasingCurve(QEasingCurve::InOutQuad);
}

void StepButton::setStepState(StepState state)
{
    if (m_state != state) {
        m_state = state;
        update(); // Перерисовываем кнопку
    }
}

StepButton::StepState StepButton::stepState() const
{
    return m_state;
}

void StepButton::setStepNumber(int number)
{
    m_stepNumber = number;
    setToolTip(m_state == StateFixed ?
                   QString("Лаб. работа %1 - Доступна").arg(number) :
                   QString("Лаб. работа %1 - В разработке").arg(number));
    update();
}

int StepButton::stepNumber() const
{
    return m_stepNumber;
}

// Реализация методов для свойства currentScale
double StepButton::currentScale() const
{
    return m_currentScale;
}

void StepButton::setCurrentScale(double scale)
{
    if (qFuzzyCompare(m_currentScale, scale))
        return;

    m_currentScale = scale;
    update();
    emit scaleChanged(scale);
}

void StepButton::paintEvent(QPaintEvent *event)
{
    Q_UNUSED(event);

    QPainter painter(this);
    painter.setRenderHint(QPainter::SmoothPixmapTransform);
    painter.setRenderHint(QPainter::Antialiasing);

    // Применяем текущий масштаб
    painter.save();
    painter.translate(width() / 2, height() / 2);
    painter.scale(m_currentScale, m_currentScale);
    painter.translate(-width() / 2, -height() / 2);

    // Рисуем соответствующее изображение
    QPixmap currentPixmap = (m_state == StateFixed) ? m_fixedStepPixmap : m_brokenStepPixmap;

    // Центрируем изображение
    int drawX = (width() - 80) / 2;
    int drawY = (height() - 80) / 2;

    painter.drawPixmap(drawX, drawY, 80, 80, currentPixmap);

    // Рисуем номер ступеньки
    painter.setPen(m_state == StateFixed ? Qt::darkGreen : Qt::darkRed);
    painter.setFont(QFont("Arial", 10, QFont::Bold));
    painter.drawText(QRect(0, height() - 20, width(), 20),
                     Qt::AlignCenter, QString::number(m_stepNumber));

    painter.restore();

    // Рисуем состояние нажатия
    if (m_isPressed) {
        painter.fillRect(rect(), QColor(0, 0, 0, 30)); // Полупрозрачный черный
    }
}

void StepButton::enterEvent(QEnterEvent *event)
{
    QWidget::enterEvent(event);
    m_isHovered = true;

    // Анимация при наведении
    m_hoverAnimation->stop();
    m_hoverAnimation->setStartValue(m_currentScale);
    m_hoverAnimation->setEndValue(1.15);
    m_hoverAnimation->start();
}

void StepButton::leaveEvent(QEvent *event)
{
    QWidget::leaveEvent(event);
    m_isHovered = false;

    // Анимация при уходе курсора
    m_hoverAnimation->stop();
    m_hoverAnimation->setStartValue(m_currentScale);
    m_hoverAnimation->setEndValue(1.0);
    m_hoverAnimation->start();

    m_isPressed = false;
    update();
}

void StepButton::mousePressEvent(QMouseEvent *event)
{
    if (event->button() == Qt::LeftButton) {
        m_isPressed = true;
        update();

        // Анимация при нажатии
        m_clickAnimation->stop();
        m_clickAnimation->setStartValue(m_currentScale);
        m_clickAnimation->setEndValue(0.9);
        m_clickAnimation->start();

        event->accept();
    } else {
        QWidget::mousePressEvent(event);
    }
}

void StepButton::mouseReleaseEvent(QMouseEvent *event)
{
    if (event->button() == Qt::LeftButton && m_isPressed) {
        m_isPressed = false;
        update();

        // Анимация при отпускании
        m_clickAnimation->stop();
        m_clickAnimation->setStartValue(m_currentScale);
        m_clickAnimation->setEndValue(m_isHovered ? 1.15 : 1.0);
        m_clickAnimation->start();

        // Испускаем сигнал клика
        emit clicked();

        event->accept();
    } else {
        QWidget::mouseReleaseEvent(event);
    }
}
