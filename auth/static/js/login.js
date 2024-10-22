function validateForm() {
    const memberId = document.getElementById('member_id').value;
    const memberPasswd = document.getElementById('member_passwd').value;
    
    if (!memberId) {
    alert('아이디를 입력해주세요!');
    document.getElementById('member_id').focus();
    return false;
    }
    
    if (!memberPasswd) {
    alert('비밀번호를 입력해주세요!');
    document.getElementById('member_passwd').focus();
    return false;
    }
    
    return true;
}

document.addEventListener('DOMContentLoaded', function() {
    const flashMessageElement = document.getElementById('flash-message');
    const flashMessage = flashMessageElement.getAttribute('data-message');
    
    if (flashMessage) {
        alert(flashMessage);  // 플래시 메시지가 있을 경우 경고창으로 표시
    }
});