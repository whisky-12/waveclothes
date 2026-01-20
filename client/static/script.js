// ========== 3D轮播核心类 ==========
class Carousel3D {
    constructor() {
        this.container = document.getElementById('carouselStage');
        this.indicators = document.getElementById('indicators');
        this.detailPanel = document.getElementById('detailPanel');
        this.startCameraBtn = document.getElementById('startCameraBtn');

        this.radius = 480; // 进一步扩大半径
        this.totalItems = 6;
        this.currentIndex = 0;
        this.isPlaying = true;
        this.autoPlayInterval = null;
        this.rotationAngle = 0;
        this.isDragging = false;
        this.startX = 0;
        this.dragStartAngle = 0;
        this.dragStartTime = 0;

        // 特效数据
        this.effects = [
            {
                id: 'studio',
                style_type: 'new_year_style',
                title: '新年烟花',
                desc: '专业新年烟花拍摄，打造完美人像效果',
                icon: '🏢',
                image: '/static/images/studio.jpg'
            },
            {
                id: 'quick',
                style_type: 'wide_format_instant_camera',
                title: '宽幅拍立得',
                desc: '双张拼接拍立得，即时生成精美照片',
                icon: '⚡',
                image: '/static/images/quick.jpg'
            },
            {
                id: 'street',
                style_type: 'winter_four_frame_grid',
                title: '冬季四宫格',
                desc: '四张冬季人像拼接，沉浸式降雪氛围',
                icon: '🏙️',
                image: '/static/images/street.jpg'
            },
            {
                id: 'nature',
                style_type: 'style4',
                title: '雪地刻印',
                desc: '俯视视角雪地照片，人物线条刻印与文字',
                icon: '🌲',
                image: '/static/images/nature.jpg'
            },
            {
                id: 'vintage',
                style_type: 'doodle_subject',
                title: '卡通涂鸦',
                desc: '手绘卡通风格叠加，混合媒体插画效果',
                icon: '📻',
                image: '/static/images/vintage.jpg'
            },
            {
                id: 'futuristic',
                style_type: 'selfie_living',
                title: '一键换装',
                desc: '全身自拍照，一键换装体验',
                icon: '🚀',
                image: '/static/images/futuristic.jpg'
            }
        ];

        this.init();
    }

    init() {
        this.createCards();
        this.createIndicators();
        this.bindEvents();
        this.updateCarousel(false);
        this.startAutoPlay();
        this.showDetail(0);
        
        // 隐藏加载动画
        setTimeout(() => {
            const loadingOverlay = document.getElementById('loadingOverlay');
            if (loadingOverlay) {
                loadingOverlay.style.display = 'none';
            }
        }, 1000);
    }

    createCards() {
        this.container.innerHTML = '';
        
        this.effects.forEach((effect, index) => {
            const card = document.createElement('div');
            card.className = 'scene-card';
            card.dataset.index = index;
            
            card.innerHTML = `
                <div class="card-inner">
                    <div class="card-face card-front">
                        <div class="card-image">
                            <div class="scene-preview">
                                <img src="${effect.image}" alt="${effect.title}" class="preview-image">
                                ${effect.id === 'quick' ? '<span class="time-badge">3秒</span>' : ''}
                            </div>
                        </div>
                         ${effect.badge ? `<div class="card-badge">${effect.badge}</div>` : ''}
                        <div class="card-content">
                            <div>
                                <h3 class="card-title">${effect.title}</h3>
                                <p class="card-desc">${effect.desc}</p>
                            </div>

                        </div>
                    </div>
                </div>
            `;

            // 点击事件
            card.addEventListener('click', () => {
                if (!this.isDragging) {
                    this.goToSlide(index);
                    this.showDetail(index);
                }
            });

            this.container.appendChild(card);
        });
    }

    createIndicators() {
        this.indicators.innerHTML = '';
        
        this.effects.forEach((_, index) => {
            const indicator = document.createElement('div');
            indicator.className = 'indicator';
            indicator.dataset.index = index;
            
            indicator.addEventListener('click', () => {
                this.goToSlide(index);
                this.showDetail(index);
            });

            this.indicators.appendChild(indicator);
        });
    }

    bindEvents() {
        // 鼠标拖拽支持
        this.container.addEventListener('mousedown', this.handleDragStart.bind(this));
        document.addEventListener('mousemove', this.handleDragMove.bind(this));
        document.addEventListener('mouseup', this.handleDragEnd.bind(this));

        // 触摸拖拽支持
        this.container.addEventListener('touchstart', this.handleDragStart.bind(this));
        document.addEventListener('touchmove', this.handleDragMove.bind(this));
        document.addEventListener('touchend', this.handleDragEnd.bind(this));

        // 鼠标悬停暂停自动播放
        this.container.addEventListener('mouseenter', () => {
            if (this.isPlaying) this.pauseAutoPlay();
        });

        this.container.addEventListener('mouseleave', () => {
            if (this.isPlaying) this.startAutoPlay();
        });

        // 指示器悬停暂停
        this.indicators.addEventListener('mouseenter', () => {
            if (this.isPlaying) this.pauseAutoPlay();
        });

        this.indicators.addEventListener('mouseleave', () => {
            if (this.isPlaying) this.startAutoPlay();
        });

        // 键盘控制
        document.addEventListener('keydown', (e) => {
            switch(e.key) {
                case 'ArrowLeft':
                    this.prev();
                    break;
                case 'ArrowRight':
                    this.next();
                    break;
            }
        });

        // 开始拍摄按钮
        if (this.startCameraBtn) {
            console.log('找到开始拍摄按钮，绑定点击事件');
            this.startCameraBtn.addEventListener('click', () => {
                console.log('开始拍摄按钮被点击，当前索引:', this.currentIndex);
                const currentEffect = this.effects[this.currentIndex];
                console.log('当前特效:', currentEffect);
                this.startCamera(currentEffect);
            });
        } else {
            console.error('未找到开始拍摄按钮！ID: startCameraBtn');
        }
    }

    handleDragStart(e) {
        this.isDragging = true;
        this.dragStartTime = Date.now();
        this.dragStartAngle = this.rotationAngle;
        
        if (e.type === 'touchstart') {
            this.startX = e.touches[0].clientX;
        } else {
            this.startX = e.clientX;
            e.preventDefault();
        }
        
        this.pauseAutoPlay();
    }

    handleDragMove(e) {
        if (!this.isDragging) return;
        
        let currentX;
        if (e.type === 'touchmove') {
            currentX = e.touches[0].clientX;
        } else {
            currentX = e.clientX;
        }
        
        const deltaX = currentX - this.startX;
        const sensitivity = 0.5; // 拖动灵敏度
        const angleOffset = -deltaX * sensitivity;
        
        this.rotationAngle = this.dragStartAngle + angleOffset;
        this.updateCarousel(true);
    }

    handleDragEnd(e) {
        if (!this.isDragging) return;
        
        this.isDragging = false;
        
        // 计算拖动距离和时间
        const dragDuration = Date.now() - this.dragStartTime;
        const velocity = Math.abs(this.rotationAngle - this.dragStartAngle) / dragDuration;
        
        // 计算应该跳转到哪个索引
        const angleStep = 360 / this.totalItems;
        const currentAngle = this.rotationAngle % 360;
        const adjustedAngle = ((currentAngle % 360) + 360) % 360;
        
        let newIndex = Math.round(adjustedAngle / angleStep) % this.totalItems;
        
        // 根据拖动方向和速度调整
        if (velocity > 1) {
            // 快速拖动，向右拖动
            newIndex = (newIndex + 1) % this.totalItems;
        } else if (velocity < -1) {
            // 快速向左拖动
            newIndex = (newIndex - 1 + this.totalItems) % this.totalItems;
        }
        
        this.goToSlide(newIndex);
        
        if (this.isPlaying) {
            this.startAutoPlay();
        }
    }

    updateCarousel(animate = true) {
        const cards = this.container.querySelectorAll('.scene-card');
        const angleStep = 360 / this.totalItems;
        
        cards.forEach((card, index) => {
            const angle = (angleStep * index) - this.rotationAngle;
            const radian = (angle * Math.PI) / 180;
            
            const x = Math.sin(radian) * this.radius;
            const z = Math.cos(radian) * this.radius;
            
            // 计算Y轴倾斜角度，让卡片面向中心
            const tiltY = -angle;
            
            card.style.transition = animate ? 'transform 0.5s cubic-bezier(0.23, 1, 0.32, 1), opacity 0.5s ease' : 'none';
            card.style.transform = `
                translate(-50%, -50%) 
                translate3d(${x}px, 0, ${z}px) 
                rotateY(${tiltY}deg)
            `;

            // 更新激活状态
            if (index === this.currentIndex) {
                card.classList.add('active');
            } else {
                card.classList.remove('active');
            }

            // 计算透明度：侧面角度范围增加180度
            const normalizedAngle = ((angle % 360) + 360) % 360;
            
            // 重新定义：正面只有很小的角度范围（345-360°和0-15°）
            // 侧面是15-165°和195-345°（大幅扩大范围）
            // 背面是165-195°（很窄的范围）
            let opacity;
            if (normalizedAngle >= 165 && normalizedAngle <= 195) {
                opacity = 0.3; // 背面（很窄的范围）
            } else if ((normalizedAngle >= 15 && normalizedAngle <= 165) || (normalizedAngle >= 195 && normalizedAngle <= 345)) {
                opacity = 0.8; // 侧面（大幅扩大范围）
            } else {
                opacity = 1.0; // 正面
            }
            
            card.style.opacity = opacity;
        });

        // 更新指示器
        const indicators = this.indicators.querySelectorAll('.indicator');
        indicators.forEach((indicator, index) => {
            indicator.classList.toggle('active', index === this.currentIndex);
        });
    }

    goToSlide(index) {
        this.currentIndex = index;
        const angleStep = 360 / this.totalItems;
        this.rotationAngle = angleStep * index;
        this.updateCarousel();
        this.showDetail(index);
    }

    next() {
        this.currentIndex = (this.currentIndex + 1) % this.totalItems;
        this.goToSlide(this.currentIndex);
    }

    prev() {
        this.currentIndex = (this.currentIndex - 1 + this.totalItems) % this.totalItems;
        this.goToSlide(this.currentIndex);
    }

    startAutoPlay() {
        if (this.autoPlayInterval) return;
        
        this.autoPlayInterval = setInterval(() => {
            this.next();
        }, 3000);
    }

    pauseAutoPlay() {
        if (this.autoPlayInterval) {
            clearInterval(this.autoPlayInterval);
            this.autoPlayInterval = null;
        }
    }

    showDetail(index) {
        const effect = this.effects[index];
        
        const detailTitle = document.getElementById('detailTitle');
        const detailDescription = document.getElementById('detailDescription');
        const detailBadge = document.getElementById('detailBadge');
        
        if (detailTitle) detailTitle.textContent = effect.title;
        if (detailDescription) detailDescription.textContent = effect.desc;
        if (detailBadge) detailBadge.textContent = effect.badge;

        // 添加淡入动画
        if (this.detailPanel) {
            this.detailPanel.style.animation = 'none';
            setTimeout(() => {
                this.detailPanel.style.animation = 'panelSlideUp 0.6s ease-out';
            }, 10);
        }
    }

    startCamera(effect) {
        console.log('========== startCamera 方法被调用 ==========');
        console.log('传入的特效对象:', effect);

        // 将特效信息存储到 localStorage
        try {
            console.log('开始准备特效数据...');
            const effectData = {
                id: effect.id,
                style_type: effect.style_type,
                title: effect.title,
                desc: effect.desc,
                badge: effect.badge
            };
            console.log('准备存储到 localStorage:', effectData);
            localStorage.setItem('selectedEffect', JSON.stringify(effectData));
            console.log('✓ 特效参数已存储到 localStorage:', effectData);

            // 验证存储是否成功
            const stored = localStorage.getItem('selectedEffect');
            console.log('✓ 验证 localStorage 读取:', stored);
        } catch (e) {
            console.error('✗ 存储特效参数失败:', e);
        }

        // 立即跳转到拍摄页面（不等待通知）
        console.log('✓ 立即跳转到拍摄页面...');
        
        // 根据特效ID判断跳转到哪个页面
        if (effect.id === 'futuristic') {
            // 客厅自拍特效跳转到专用页面
            window.location.href = '/ai-camera-living.html';
        } else {
            // 其他特效跳转到通用拍摄页面
            window.location.href = '/ai-camera-demo.html';
        }
        console.log('✓ 跳转命令已执行');
    }

    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <span class="notification-icon">${type === 'success' ? '✓' : 'ℹ'}</span>
            <span class="notification-text">${message}</span>
        `;

        Object.assign(notification.style, {
            position: 'fixed',
            top: '100px',
            right: '30px',
            padding: '16px 24px',
            background: 'rgba(255, 255, 255, 0.1)',
            backdropFilter: 'blur(20px)',
            border: '1px solid rgba(255, 255, 255, 0.2)',
            borderRadius: '12px',
            color: 'white',
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
            zIndex: '9999',
            opacity: '0',
            transform: 'translateX(100px)',
            transition: 'all 0.4s cubic-bezier(0.4, 0, 0.2, 1)'
        });

        document.body.appendChild(notification);

        setTimeout(() => {
            notification.style.opacity = '1';
            notification.style.transform = 'translateX(0)';
        }, 100);

        setTimeout(() => {
            notification.style.opacity = '0';
            notification.style.transform = 'translateX(100px)';
            setTimeout(() => notification.remove(), 400);
        }, 3000);
    }
}

// ========== 页面加载完成后初始化 ==========
document.addEventListener('DOMContentLoaded', () => {
    console.log('页面加载完成，开始初始化轮播...');

    // 初始化3D轮播
    const carousel = new Carousel3D();
    console.log('轮播初始化完成');

    // 添加页面加载动画
    document.body.style.opacity = '0';
    setTimeout(() => {
        document.body.style.transition = 'opacity 1s ease-in-out';
        document.body.style.opacity = '1';
    }, 100);

    // 窗口大小改变时重新计算
    window.addEventListener('resize', debounce(() => {
        carousel.updateCarousel(false);
    }, 250));
});

// ========== 工具函数 ==========
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}
