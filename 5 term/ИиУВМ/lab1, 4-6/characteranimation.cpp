#include "characteranimation.h"
#include <QPainter>
#include <QDebug>

CharacterAnimation::CharacterAnimation(QWidget *parent)
    : QWidget(parent), m_frameWidth(0), m_frameHeight(0), m_currentFrame(0),
    m_totalFrames(0), m_columns(0), m_scaleFactor(1.0), m_backgroundColor(Qt::transparent)
{
    m_animationTimer = new QTimer(this);
    connect(m_animationTimer, &QTimer::timeout, this, &CharacterAnimation::updateFrame);
    setMinimumSize(100, 100);
}

bool CharacterAnimation::loadSpriteSheet(const QString &imagePath, int frameWidth, int frameHeight)
{
    if (m_spriteSheet.load(imagePath)) {
        m_frameWidth = frameWidth;
        m_frameHeight = frameHeight;
        calculateTotalFrames();
        update();
        return true;
    }
    return false;
}

void CharacterAnimation::calculateTotalFrames()
{
    if (m_spriteSheet.isNull() || m_frameWidth == 0 || m_frameHeight == 0) {
        m_totalFrames = 0;
        m_columns = 0;
        return;
    }
    m_columns = m_spriteSheet.width() / m_frameWidth;
    int rows = m_spriteSheet.height() / m_frameHeight;
    m_totalFrames = m_columns * rows;
}

void CharacterAnimation::setAnimationSpeed(int ms) { m_animationTimer->setInterval(ms); }
void CharacterAnimation::startAnimation() { if (m_totalFrames > 0) { m_animationTimer->start(); emit animationStarted(); } }
void CharacterAnimation::stopAnimation() { m_animationTimer->stop(); m_currentFrame = 0; update(); emit animationStopped(); }
void CharacterAnimation::pauseAnimation() { m_animationTimer->stop(); }
void CharacterAnimation::setFrame(int frame) { if (frame >= 0 && frame < m_totalFrames) { m_currentFrame = frame; update(); emit frameChanged(frame); } }
int CharacterAnimation::currentFrame() const { return m_currentFrame; }
int CharacterAnimation::totalFrames() const { return m_totalFrames; }
void CharacterAnimation::setScaleFactor(double scale) { m_scaleFactor = scale; update(); }
void CharacterAnimation::setBackgroundColor(const QColor &color) { m_backgroundColor = color; update(); }

void CharacterAnimation::updateFrame()
{
    if (m_totalFrames == 0) return;
    m_currentFrame = (m_currentFrame + 1) % m_totalFrames;
    update();
    emit frameChanged(m_currentFrame);
}

void CharacterAnimation::paintEvent(QPaintEvent *event)
{
    Q_UNUSED(event);
    QPainter painter(this);
    painter.setRenderHint(QPainter::SmoothPixmapTransform);

    if (m_backgroundColor != Qt::transparent) {
        painter.fillRect(rect(), m_backgroundColor);
    }

    if (m_spriteSheet.isNull() || m_totalFrames == 0) {
        painter.drawText(rect(), Qt::AlignCenter, "Загрузите спрайтшит");
        return;
    }

    int frameX = (m_currentFrame % m_columns) * m_frameWidth;
    int frameY = (m_currentFrame / m_columns) * m_frameHeight;
    int drawWidth = m_frameWidth * m_scaleFactor;
    int drawHeight = m_frameHeight * m_scaleFactor;
    int x = (width() - drawWidth) / 2;
    int y = (height() - drawHeight) / 2;

    QRect frameRect(frameX, frameY, m_frameWidth, m_frameHeight);
    QRect targetRect(x, y, drawWidth, drawHeight);
    painter.drawPixmap(targetRect, m_spriteSheet, frameRect);
}

QSize CharacterAnimation::sizeHint() const
{
    return QSize(m_frameWidth * m_scaleFactor + 20, m_frameHeight * m_scaleFactor + 20);
}
