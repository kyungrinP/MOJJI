document.addEventListener('DOMContentLoaded', function () {
    var mySwiper = new Swiper('.swiper-container', {
        autoplay: {
            delay: 2000,
            disableOnInteraction: false,
        },
        loop: true,
        slidesPerView: 3,
        pagination: {
            el: '.swiper-pagination',
            clickable: true,
        },
        navigation: {
            nextEl: '.slide-next',
            prevEl: '.slide-prev',
        },
        breakpoints: {
            480: {
                slidesPerView: 1,
            },
        },
        on: {
            init: function() {
                this.slides.forEach((slide, index) => {
                    slide.style.transform = (index === 1) ? 'scale(1)' : 'scale(0.8)';
                });
            },
            slideChange: function () {
                this.slides.forEach((slide) => {
                    slide.style.transform = 'scale(0.8)';
                });

                const secondSlideIndex = (this.activeIndex + 1) % this.slides.length;
                const slideToHighlight = this.slides[secondSlideIndex];
                if (slideToHighlight) {
                    slideToHighlight.style.transform = 'scale(1)';
                }
            },
            resize: function () {
                const screenWidth = window.innerWidth;
                if (screenWidth <= 430) {
                    this.params.slidesPerView = 1;
                } else {
                    this.params.slidesPerView = 3;
                }
                this.update();
            }
        }
    });

    window.addEventListener('resize', function() {
        mySwiper.emit('resize');
    });
});

document.getElementById('fileInput').addEventListener('change', function() {
    var form = this.closest('form');
    if(this.files.length > 0) {
        form.submit();
    }
});