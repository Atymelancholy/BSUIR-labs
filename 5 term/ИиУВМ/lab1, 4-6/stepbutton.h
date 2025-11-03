#ifndef STEPBUTTON_H
#define STEPBUTTON_H

#include <QWidget>
#include <QPixmap>
#include <QPropertyAnimation>
#include <QEasingCurve>

class StepButton : public QWidget
{
    Q_OBJECT
    // Добавляем свойство для анимации
    Q_PROPERTY(double currentScale READ currentScale WRITE setCurrentScale NOTIFY scaleChanged)

public:
    enum StepState {
        StateFixed,    // Целая ступенька
        StateBroken    // Сломанная ступенька
    };

    explicit StepButton(QWidget *parent = nullptr);
    StepButton(StepState state, int number, QWidget *parent = nullptr);

    void setStepState(StepState state);
    StepState stepState() const;

    void setStepNumber(int number);
    int stepNumber() const;

    // Добавляем методы для свойства
    double currentScale() const;
    void setCurrentScale(double scale);

signals:
    void clicked();
    void scaleChanged(double scale); // Сигнал для изменения масштаба

protected:
    void paintEvent(QPaintEvent *event) override;
    void enterEvent(QEnterEvent *event) override;
    void leaveEvent(QEvent *event) override;
    void mousePressEvent(QMouseEvent *event) override;
    void mouseReleaseEvent(QMouseEvent *event) override;

private:
    void setupAnimations();
    void loadStepImages();

    StepState m_state;
    int m_stepNumber;
    bool m_isPressed;
    bool m_isHovered;

    QPixmap m_fixedStepPixmap;
    QPixmap m_brokenStepPixmap;

    QPropertyAnimation *m_hoverAnimation;
    QPropertyAnimation *m_clickAnimation;
    double m_currentScale;
};

#endif // STEPBUTTON_H
