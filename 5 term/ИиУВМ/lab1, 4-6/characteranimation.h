#ifndef CHARACTERANIMATION_H
#define CHARACTERANIMATION_H

#include <QWidget>
#include <QTimer>
#include <QPixmap>

class CharacterAnimation : public QWidget
{
    Q_OBJECT

public:
    explicit CharacterAnimation(QWidget *parent = nullptr); // Добавляем explicit

    void loadSpriteSheet(const QString &imagePath, int frameWidth, int frameHeight);
    void setAnimationSpeed(int ms);
    void startAnimation();
    void stopAnimation();
    void pauseAnimation();
    void setFrame(int frame);
    int currentFrame() const;
    int totalFrames() const;
    void setScaleFactor(double scale);
    void setBackgroundColor(const QColor &color);

signals:
    void animationStarted();
    void animationStopped();
    void frameChanged(int frame);

protected:
    void paintEvent(QPaintEvent *event) override;
    QSize sizeHint() const override;

private:
    void calculateTotalFrames();
    void updateFrame();

    QPixmap m_spriteSheet;
    QTimer *m_animationTimer;
    int m_frameWidth;
    int m_frameHeight;
    int m_currentFrame;
    int m_totalFrames;
    int m_columns;
    double m_scaleFactor;
    QColor m_backgroundColor;
};

#endif // CHARACTERANIMATION_H
