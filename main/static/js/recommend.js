document.addEventListener('DOMContentLoaded', function() {
    const rotateIcon = document.getElementById('rotate');
    const recomContainer = document.getElementById('recom_container');
    const imageElements = JSON.parse(document.getElementById('imageElements').textContent);
    const savedFavorites = JSON.parse(document.getElementById('savedFavorites').textContent);
    let currentIndex = 0;

    function displayImages() {
        recomContainer.innerHTML = '';
        for (let i = 0; i < 3; i++) {
            const index = (currentIndex + i) % imageElements.length;
            const imageElement = imageElements[index];
            const imageContainer = document.createElement('div');
            imageContainer.classList.add('image-container');

            const anchor = document.createElement('a');
            anchor.href = imageElement.href;
            anchor.target = '_blank';

            const img = document.createElement('img');
            img.src = imageElement.src;
            img.alt = '추천코디';
            img.classList.add('recom_codi');

            const heartIcon = document.createElement('i');
            heartIcon.classList.add('fa-regular', 'fa-heart', 'heart-frame', 'heart-icon');
            heartIcon.dataset.src = imageElement.src;
            heartIcon.dataset.href = imageElement.href;

            // 하트 아이콘 상태 설정
            if (savedFavorites.includes(imageElement.href)) {
                heartIcon.classList.remove('fa-regular');
                heartIcon.classList.add('fa-solid');
            }

            anchor.appendChild(img);
            imageContainer.appendChild(anchor);
            imageContainer.appendChild(heartIcon);
            recomContainer.appendChild(imageContainer);
        }
    }

    rotateIcon.addEventListener('click', function() {
        currentIndex = (currentIndex + 3) % imageElements.length;
        displayImages();
    });

    // 처음 이미지를 표시합니다.
    displayImages();

    // 하트 아이콘 클릭 이벤트
    recomContainer.addEventListener('click', function(event) {
        if (event.target.classList.contains('heart-icon')) {
            const heartIcon = event.target;
            const userID = document.getElementById('userID').textContent;
            const imageUrl = heartIcon.dataset.src;
            const imageHref = heartIcon.dataset.href;
            const fileName = heartIcon.dataset.filename;

            if (!userID) {
                if (confirm('로그인 후 이용할 수 있습니다.\n로그인 페이지로 이동하시겠습니까?')) {
                    window.location.href = '/login';
                }
                return;
            }

            let action = 'save';
            if (heartIcon.classList.contains('fa-solid')) {
                action = 'delete';
            }

            fetch('/favorite', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    action: action,
                    userID: userID,
                    image: imageUrl,
                    href: imageHref,
                    file_name: fileName
                })
            })
            .then(response => {
                if (response.ok) {
                    return response.json();
                } else {
                    throw new Error('네트워크 응답이 올바르지 않습니다.');
                }
            })
            .then(data => {
                if (data.success) {
                    if (action === 'save') {
                        heartIcon.dataset.filename = data.file_name;
                        heartIcon.classList.remove('fa-regular');
                        heartIcon.classList.add('fa-solid');
                        savedFavorites.push(imageHref); // Update savedFavorites
                    } else {
                        heartIcon.classList.remove('fa-solid');
                        heartIcon.classList.add('fa-regular');
                        const index = savedFavorites.indexOf(imageHref); // Update savedFavorites
                        if (index > -1) {
                            savedFavorites.splice(index, 1);
                        }
                    }
                } else {
                    throw new Error(data.message);
                }
            })
            .catch(error => {
                console.error('에러 발생:', error.message);
            });
        }
    });
});