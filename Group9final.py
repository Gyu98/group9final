import speech_recognition as sr
#음성을 인식해주는 패키지
import matplotlib.pyplot as plt
#수식의 Ploy을 찍어줘 시각화해주는 패키지
import numpy as np
#배열 사용 패키지
import math
#수식사용 패키지
import pandas as pd
#배열 사용패키지
from pandas_datareader import data
#크롤링 패키지
pd.options.mode.chained_assignment = None  # default='warn'
#Pandas 사용할때 할당의 오류를 제거해주는 코드
import pickle
#텍스트 형식이 아닌 파이썬 자체를 객체로 저장하게 만드는 코드

def stock_addition(A, B, C):  # 주식의 종가와 예측가를 저장해줍니다.
    try:
        with open('word.txt', 'rb') as f:
            #file을 읽기 전용으로 읽어냅니다.
            stock = pickle.load(f)
            #pickle함수를 사용하여 텍스트를 객체로 지정해 불러옵니다.
        with open('word.txt', 'wb') as f:
            #file을 쓰기 전용으로 불러옵니다.
            stock[A] = (B,C)
            #stock에서 주식종목명을 배열화해서 추가함
            pickle.dump(stock, f)
            #추가 후 주식을 돌려놓음
    except:
        #파일이 열리지 않는, 즉 txt파일이 존재하지 않는경우
        with open('word.txt', 'wb') as f:
            #txt파일을 생성해줍니다.
            pickle.dump({A: B}, f)

def stockbook():  #저장된 주식의 종가와 예측가격을 출력합니다.
    try:
        #txt파일로 되어있는 파일을 pickle로 불러내어 딕셔너리 형태로 출력
        with open('word.txt', 'rb') as f:
            stock = pickle.load(f)
            for key, val in stock.items():
                print("{key} -> 현재주가,예상주가: {value}".format(key=key, value=val))
                #주가가 출력되게 함
    except FileNotFoundError:
        print("저장되지 않았습니다.")
        #파일이 저장되지 않았을 때 저장되지 않았다고 출력
def crawling(search):
    # 종목 타입에 따라 download url이 다름. 종목코드 뒤에 .KS .KQ등이 입력되어야해서 Download Link 구분 필요
    stock_type = {
        'kospi':'stockMkt',
        'kosdaq':'kosdaqMkt'
    }

    # 회사명으로 주식 종목 코드를 획득할 수 있도록 하는 함수
    # 주식 종목 코드를 획득 후 종목 명과 연결시켜주기 위함
    # download url 조합
    def get_download_stock(market_type=None):
        market_type_ = stock_type[market_type]
    #위에서 선언한 시장의 종목 타입에 따라 url 구분을 해줌
        download_link = 'http://kind.krx.co.kr/corpgeneral/corpList.do'
        download_link = download_link + '?method=download'
        download_link = download_link + '&marketType=' + market_type_
        code = pd.read_html(download_link, header=0)[0]
        return code

    # kospi 종목코드 목록 다운로드
    def get_download_kospi():
        find = get_download_stock('kospi')
        #다운받은 종목
        find.종목코드 = find.종목코드.map('{:06d}.KS'.format)
        #종목코드를 찾아 find.종목코드에 넣음
        return find

    # kosdaq 종목코드 목록 다운로드
    def get_download_kosdaq():
        find = get_download_stock('kosdaq')
        #다운받은 종목
        find.종목코드 = find.종목코드.map('{:06d}.KQ'.format)
        return find
    # kospi, kosdaq 종목코드 각각 다운로드
    kospi_df = get_download_kospi()
    kosdaq_df = get_download_kosdaq()
    # data frame merge
    code_df = pd.concat([kosdaq_df, kospi_df])

    # data frame정리
    code_df = code_df[['회사명', '종목코드']]
    # data frame title 변경 '회사명' = name, 종목코드 = 'code'
    code_df = code_df.rename(columns={'회사명': 'name', '종목코드': 'code'})
    def get_code(df, name):
        #코드와 종목명을 추출
        code = df.query("name=='{}'".format(name))['code'].to_string(index=False)
        # 위와같이 code명을 가져오면 앞에 공백이 붙어있는 상황이 발생하여 앞뒤로 strip() 하여 공백 제거
        code = code.strip()
        return code
    code = get_code(code_df, search)
    # get_data_yahoo API를 통해서 yahho finance의 주식 종목 데이터를 가져온다.
    df = data.DataReader(code, 'yahoo', start='2020-1-1')
    #2020년 부터의 데이터를 코드를 통해 추출
    df_ = df[:]
    #현재까지의 데이터로 한정
    df['Close'].plot()
    #종가까지의 데이터를 그래프로출력
    days = (df_.index[-1] - df_.index[0]).days
    #현재부터 지금까지 영업일 수 계산
    mu = ((((df_['Close'][-1]) / df_['Close'][1])) ** (365.0 / days)) - 1
    #연간평균수익률 계산
    print('mu =', str(round(mu, 4) * 100) + "%")
    # 주가 수익률의 연간 volatility 계산해주기
    df_['Returns'] = df_['Adj Close'].pct_change()
    vol = df_['Returns'].std() * math.sqrt(252)
    print("Annual Volatility =", str(round(vol, 4) * 100) + "%")

    result = []
    S = df_['Close'][-1]
    T = 252  # 1년 영업일 기준 일 수
    dt = 1 / T
    s_path_multi = np.zeros(shape=(1000, 30))
    # 30영업일 이후
    s_path_multi[:, 0] = S

    for i in range(1000):
        #1000번의 같은 몬테카를로 시행
        Z = np.random.standard_normal(size=1000)
        for j in range(1, 30):  # 배열 크기에 따라 기간
            s_path_multi[i, j] = s_path_multi[i, j - 1] * np.exp((mu - 0.5 * vol ** 2) * dt + vol * np.sqrt(dt) * Z[j])
        result.append(s_path_multi[i, -1])
    #다음과 같은 G.V.M 모델을 기반으로 몬테카를로 시행
    print("금일 ", search, "주가", S)
    print("몬테카를로 시뮬레이션으로 계산한 30 영업일 뒤 주가", search, "주가", round(np.mean(result), 2))
    #예측 주가는 모든 몬테카를로 시뮬레이션의 평균
    # 주가 그래프를 그려주는 코드입니다.
    plt.figure(figsize=(10, 8))

    for i in range(s_path_multi.shape[0]):
        plt.plot(s_path_multi[i], color='b', linewidth=1.0)
    #몬테카를로 시행의 그래프 출력 (가시화)
    plt.xlabel('Time')
    plt.ylabel('Interest rate')
    plt.grid(True)
    plt.axis('tight')
    plt.show()
    plt.hist(result, bins=50)
    plt.show()
    #히스토그램 화
    add = input("종목에 추가하시겠습니까? y/n: ")
    if (add == 'y' or add == 'Y'):
        stock_addition(search, S, round(np.mean(result), 2))
        #stock addtion 함수를 통해 저장
        print('추가되었습니다.')


def stock_simulation():  # 주식 시뮬레이션을 합니다. search변수에 받아서 crawiling함수로 보내줍니다.
    print("====================================")
    print("1.음성인식 2. 직접입력 ")
    #음성인식과 직접입력중 선택하게함
    print("====================================")
    choice =int(input())
    if(choice==1):
        print("주식을 말하세요!")
        rec = sr.Recognizer()
        mic = sr.Microphone()
        with mic as source:
            audio = rec.listen(source)
            #녹음하게 함
        search = rec.recognize_google(audio, language='ko-KR')
        #구글에 검색하게함
        search = search.replace(" ",'')
        # replace 함수를 통해 모든 공백 제거 , SK 하이닉스 등 영문, 한문 섞여있는 종목 시행 시 중간에 공백이 생겨 코드 확인 및 크롤링이 안되었기 때문.
        print(search)
        crawling(search)
        #crawling 함수 시행
    elif (choice==2):
        search = input("주식을 입력해주세요! : ")
        crawling(search)
while (1):
    #무한반복문에 넣어 종료시까지 시행
    print("====================================")
    print("1.종목 출력 2.시뮬레이션 3.종료  ")
    print("====================================")
    n = int(input("번호를 선택하세요 : "))
    if (n == 1):
        stockbook()
    elif (n == 2):
        stock_simulation()
    elif (n == 3):
        break