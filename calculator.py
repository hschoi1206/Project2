# 간단한 사칙연산 계산기
# 사용법: "숫자 연산자 숫자" 형식으로 입력 (예: 3 + 5), 종료는 q


def calculate(a, op, b):
    """두 숫자 a, b에 연산자 op를 적용한 결과를 반환한다."""
    if op == "+":
        return a + b
    elif op == "-":
        return a - b
    elif op == "*":
        return a * b
    elif op == "/":
        if b == 0:
            raise ZeroDivisionError("0으로 나눌 수 없습니다.")
        return a / b
    else:
        raise ValueError(f"지원하지 않는 연산자입니다: {op}")


def main():
    print("=== 계산기 ===")
    print("예: 3 + 5  (지원 연산자: + - * /, 종료: q)")

    while True:
        line = input("> ").strip()

        if line.lower() == "q":
            print("계산기를 종료합니다.")
            break

        parts = line.split()
        if len(parts) != 3:
            print("형식 오류: '숫자 연산자 숫자'처럼 띄어쓰기로 입력하세요.")
            continue

        try:
            a = float(parts[0])
            op = parts[1]
            b = float(parts[2])
            result = calculate(a, op, b)
            # 정수로 딱 떨어지면 소수점 없이 출력 (8.0 -> 8)
            if result == int(result):
                result = int(result)
            print(f"= {result}")
        except ValueError as e:
            print(f"입력 오류: {e}")
        except ZeroDivisionError as e:
            print(f"계산 오류: {e}")


if __name__ == "__main__":
    main()
