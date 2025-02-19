## 실시간 측정값

페이지: `Data -> Live Measurements`

로그인 후 사용자가 처음 보게 되는 페이지는 `Live Measurements` 페이지입니다. 이 페이지는 Input 및 Function 컨트롤러로부터 수집된 현재 측정값을 표시합니다. 만약 `Live` 페이지에 아무런 내용이 표시되지 않는다면, Input 또는 Function 컨트롤러가 올바르게 구성되고 활성화되었는지 확인하세요. 측정 데이터베이스로부터 데이터가 자동으로 페이지에 업데이트됩니다.

## 비동기 그래프

페이지: `Data -> Asynchronous Graphs`

비동기 그래프는 수 주/월/년 등 비교적 긴 기간에 걸친 데이터 집합을 시각화할 때 유용한 그래픽 데이터 디스플레이입니다. 동기식 그래프로 볼 경우, 데이터와 프로세서에 매우 큰 부하가 걸릴 수 있습니다. 시간 범위를 선택하면 해당 기간의 데이터가 존재할 경우 불러와집니다. 첫 번째 뷰는 선택한 전체 데이터 집합을 보여줍니다. 각 뷰/줌마다 700개의 데이터 포인트가 로드됩니다. 만약 선택한 기간 동안 700개 이상의 데이터 포인트가 기록되어 있다면, 해당 기간의 데이터를 평균내어 700개의 포인트로 생성됩니다. 이를 통해 방대한 데이터 집합을 탐색할 때 훨씬 적은 데이터만 사용하게 됩니다. 예를 들어, 4개월 치 데이터가 모두 다운로드되면 10메가바이트가 될 수 있지만, 4개월 기간을 볼 때는 10메가바이트의 모든 데이터를 확인할 수 없으며, 포인트를 집계하는 것이 필수적입니다. 비동기 방식으로 데이터를 로드하면, 화면에 보이는 데이터만 다운로드됩니다. 따라서 매번 그래프를 로드할 때 10메가바이트를 다운로드하는 대신, 새로운 줌 레벨이 선택될 때까지 약 50KB만 다운로드됩니다.

!!! 주의
    그래프를 표시하려면 측정값이 필요하므로, 최소한 하나의 Input/Output/Function 등이 추가되고 활성화되어야 합니다.

## 대시보드

페이지: `Data -> Dashboard`

대시보드는 다양한 대시보드 위젯 덕분에 데이터를 시각화하고 시스템을 조작하는 데 모두 사용할 수 있습니다. 여러 개의 대시보드를 생성할 수 있으며, 배열 변경을 방지하기 위해 잠글 수도 있습니다.

## 위젯

위젯은 대시보드 상의 요소로서, 데이터 시각화(차트, 지표, 게이지 등)나 시스템과의 상호작용(출력 제어, PWM 듀티 사이클 변경, 데이터베이스 조회 또는 수정 등)과 같은 다양한 용도로 사용됩니다. 위젯은 드래그 앤 드롭으로 손쉽게 재배치하거나 크기를 조정할 수 있습니다. 지원되는 위젯의 전체 목록은 [Supported Widgets](Supported-Widgets.md)를 참조하세요.

### 커스텀 위젯

Looperget에는 사용자가 직접 만든 위젯을 Looperget 시스템 내에서 사용할 수 있도록 하는 커스텀 위젯 가져오기(import) 시스템이 있습니다. 커스텀 위젯은 `[Gear Icon] -> Configure -> Custom Widgets` 페이지에서 업로드할 수 있으며, 가져온 후에는 `Setup -> Widget` 페이지에서 사용할 수 있게 됩니다.

작동하는 모듈을 개발하셨다면, [새 GitHub 이슈 만들기](https://github.com/aot-inc/Looperget/issues/new?assignees=&labels=&template=feature-request.md&title=New%20Module) 또는 풀 리퀘스트를 고려해 주세요. 그러면 내장 세트에 포함될 수도 있습니다.

적절한 형식을 확인하려면, 디렉터리 [Looperget/looperget/widgets](https://github.com/aot-inc/Looperget/tree/master/looperget/widgets/)에 있는 내장 위젯 모듈을 열어보세요. 또한, 디렉터리 [Looperget/looperget/widgets/examples](https://github.com/aot-inc/Looperget/tree/master/looperget/widgets/examples)에는 예제 커스텀 위젯들도 있습니다.

커스텀 위젯 모듈을 생성할 때는 보통 Javascript의 특정 배치 및 실행이 필요합니다. 이를 위해 각 모듈에서는 몇 가지 변수가 생성되었으며, 이는 여러 위젯이 표시될 대시보드 페이지의 간략한 구조를 따릅니다.

```angular2html
<html>
<head>
  <title>Title</title>
  <script>
    {{ widget_1_dashboard_head }}
    {{ widget_2_dashboard_head }}
  </script>
</head>
<body>

<div id="widget_1">
  <div id="widget_1_titlebar">{{ widget_dashboard_title_bar }}</div>
  {{ widget_1_dashboard_body }}
  <script>
    $(document).ready(function() {
      {{ widget_1_dashboard_js_ready_end }}
    });
  </script>
</div>

<div id="widget_2">
  <div id="widget_2_titlebar">{{ widget_dashboard_title_bar }}</div>
  {{ widget_2_dashboard_body }}
  <script>
    $(document).ready(function() {
      {{ widget_2_dashboard_js_ready_end }}
    });
  </script>
</div>

<script>
  {{ widget_1_dashboard_js }}
  {{ widget_2_dashboard_js }}

  $(document).ready(function() {
    {{ widget_1_dashboard_js_ready }}
    {{ widget_2_dashboard_js_ready }}
  });
</script>

</body>
</html>
```
