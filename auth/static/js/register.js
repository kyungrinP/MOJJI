// 비밀번호 input 요소
var passwdInput = document.getElementById('passwd');

// 툴팁 요소
var tooltip = document.querySelector('.ec-base-tooltip.typeUpper');

// 비밀번호 input을 클릭할 때 툴팁을 표시
passwdInput.addEventListener('focus', function(event) {
  tooltip.style.display = 'block';
  event.stopPropagation(); // 클릭 이벤트 전파 방지
});

// 비밀번호 input에서 포커스가 벗어날 때 툴팁을 숨김
passwdInput.addEventListener('blur', function(event) {
  tooltip.style.display = 'none';
});

// 비밀번호 일치 확인 함수
function checkPasswordMatch() {
  var password = document.getElementById("passwd").value;
  var confirmPassword = document.getElementById("user_passwd_confirm").value;
  var message = document.getElementById("pwConfirmMsg");

  if (password !== confirmPassword) {
    message.textContent = "비밀번호가 일치하지 않습니다.";
    message.style.color = "red";
  } else {
    message.textContent = "";
  }
}

// 아이디 중복 확인 함수
function checkDuplicateId() {
  var memberId = document.getElementById('member_id').value;
  var idRegex = /^(?=.*[a-z])(?=.*\d)[a-z\d]{4,16}$/;

  if (!idRegex.test(memberId)) {
    alert('아이디 입력 조건이 충족하지 않습니다.');
    document.getElementById('idDuplication').value = 'idUncheck';
    document.getElementById('member_id').focus();
    return;
  }

  fetch(`http://127.0.0.1:5000/auth/check-id?member_id=${memberId}`)
    .then(response => response.json())
    .then(data => {
      if (data.exists) {
        alert('다른 아이디를 사용해주세요.');
        document.getElementById('idDuplication').value = 'idUncheck';
      } else {
        alert('사용 가능한 아이디입니다.');
        document.getElementById('idDuplication').value = 'idChecked';
      }
    })
    .catch(error => {
      console.error('Error:', error);
    });
}

// 이메일 유효성 검사 함수
function validateEmail() {
  const emailInput = document.getElementById('email1');
  const emailMsg = document.getElementById('emailMsg');
  const emailPattern = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;

  if (emailPattern.test(emailInput.value)) {
    emailMsg.textContent = '';
  } else {
    emailMsg.textContent = '이메일 형식이 잘못되었습니다. 예: hello@mojji.com';
    emailMsg.style.color = 'red';
  }
}

// 폼 제출 전 검사
async function checkForm(event) {
  event.preventDefault(); // 폼 제출 기본 동작 중지

  const email = document.getElementById('email1').value;
  const emailMsg = document.getElementById("emailMsg");
  const emailPattern = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;

  if (!emailPattern.test(email)) {
    if (emailMsg) {
      emailMsg.textContent = '이메일 형식이 잘못되었습니다. 예: hello@mojji.com';
      emailMsg.style.color = 'red';
    }
    document.getElementById('email1').focus();
    alert('이메일 형식이 잘못되었습니다.');
    return false;
  } else {
    if (emailMsg) {
      emailMsg.textContent = '';
    }
  }

  const idDuplication = document.getElementById('idDuplication').value;
  if (idDuplication !== 'idChecked') {
    alert('아이디 중복 확인을 클릭해주세요.');
    return false;
  }

  const id = document.getElementById('member_id').value;
  const idMsg = document.getElementById('idMsg');
  var idRegex = /^(?=.*[a-z])(?=.*\d)[a-z\d]{4,16}$/;

  if (!idRegex.test(id)) {
    if (idMsg) {
      idMsg.textContent = '영문소문자/숫자 조합, 4~16자';
      idMsg.style.color = 'red';
    }
    document.getElementById('member_id').focus();
    return false;
  } else {
    if (idMsg) {
      idMsg.textContent = '';
    }
  }

  const password = document.getElementById('passwd').value;
  const confirmPassword = document.getElementById('user_passwd_confirm').value;

  if (password !== confirmPassword) {
    alert('비밀번호가 일치하지 않습니다.');
    document.getElementById('user_passwd_confirm').focus();
    return false;
  }

  const postcode = document.getElementById('postcode1').value;
  if (!postcode) {
    alert('주소를 입력해주세요.');
    document.getElementById('postcode1').focus();
    return false;
  }

  const mobile = document.getElementById('mobile1').value + document.getElementById('mobile2').value + document.getElementById('mobile3').value;

  if (mobile.length !== 11) {
    alert('핸드폰 번호가 올바르지 않습니다.');
    return false;
  }

  try {
    const mobileResponse = await fetch(`http://127.0.0.1:5000/auth/check-mobile?mobile=${mobile}`);
    const mobileData = await mobileResponse.json();

    if (mobileData.valid) {
      alert('이미 사용 중인 휴대전화 번호입니다.');
      document.getElementById('mobile2').focus();
      document.getElementById('mobile2').value = '';
      document.getElementById('mobile3').value = '';
      return false;
    }

    const response = await fetch(`http://127.0.0.1:5000/auth/check-pw?passwd=${password}`);
    const data = await response.json();

    if (!data.valid) {
      alert('비밀번호 입력 조건이 충족하지 않습니다.');
      document.getElementById('passwd').focus();
      document.getElementById('passwd').value = '';
      document.getElementById('user_passwd_confirm').value = '';
      return false;
    }

    const emailResponse = await fetch(`http://127.0.0.1:5000/auth/check-email?email=${email}`);
    const emailData = await emailResponse.json();

    if (emailData.valid) {
      alert('이미 사용 중인 이메일입니다.');
      document.getElementById('email1').focus();
      document.getElementById('email1').value = '';
      return false;
    }

    alert(`환영합니다. ${id}님`);
    document.getElementById('registerForm').submit();
  } catch (error) {
    console.error('Error:', error);
    alert('서버와의 통신 중 오류가 발생했습니다.');
    return false;
  }
}

// 폼에 이벤트 리스너 추가
document.getElementById('registerForm').addEventListener('submit', checkForm);

// 아이디 입력 실시간 검증
document.getElementById('member_id').addEventListener('input', function() {
  var id = this.value;
  var idMsg = document.getElementById('idMsg');
  var regex = /^(?=.*[a-z])(?=.*\d)[a-z\d]{4,16}$/;

  if (!regex.test(id)) {
    idMsg.textContent = '영문소문자/숫자 조합, 4~16자';
    idMsg.style.color = 'red';
  } else {
    idMsg.textContent = '';
  }
});

// 우편번호 API 호출
function sample6_execDaumPostcode() {
  new daum.Postcode({
    oncomplete: function(data) {
      var addr = '';
      var extraAddr = '';

      if (data.userSelectedType === 'R') {
        addr = data.roadAddress;
      } else {
        addr = data.jibunAddress;
      }

      if (data.userSelectedType === 'R') {
        if (data.bname !== '' && /[동|로|가]$/g.test(data.bname)) {
          extraAddr += data.bname;
        }
        if (data.buildingName !== '' && data.apartment === 'Y') {
          extraAddr += (extraAddr !== '' ? ', ' + data.buildingName : data.buildingName);
        }
        if (extraAddr !== '') {
          extraAddr = ' (' + extraAddr + ')';
        }
        document.getElementById("extraAddress").value = extraAddr;
      } else {
        document.getElementById("extraAddress").value = '';
      }

      document.getElementById('postcode1').value = data.zonecode;
      document.getElementById("addr1").value = addr;
      document.getElementById("addr2").focus();
    }
  }).open();
}