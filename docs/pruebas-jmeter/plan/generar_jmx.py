"""Genera plan/netsentinel.jmx. Propiedades: host, port, users, rampup, duration, think_ms, user, password (nunca se escriben en el JMX)."""
from xml.sax.saxutils import escape as e

def http(name, path, method="GET", body=None, extra=""):
    b = ""
    if body is not None:
        b = (f'<boolProp name="HTTPSampler.postBodyRaw">true</boolProp><elementProp name="HTTPsampler.Arguments" elementType="Arguments"><collectionProp name="Arguments.arguments"><elementProp name="" elementType="HTTPArgument"><boolProp name="HTTPArgument.always_encode">false</boolProp><stringProp name="Argument.value">{e(body)}</stringProp><stringProp name="Argument.metadata">=</stringProp></elementProp></collectionProp></elementProp>')
    return f'''<HTTPSamplerProxy guiclass="HttpTestSampleGui" testclass="HTTPSamplerProxy" testname="{e(name)}" enabled="true">{b}
<stringProp name="HTTPSampler.domain">${{__P(host,localhost)}}</stringProp><stringProp name="HTTPSampler.port">${{__P(port,5173)}}</stringProp>
<stringProp name="HTTPSampler.path">{e(path)}</stringProp><stringProp name="HTTPSampler.method">{method}</stringProp>
<boolProp name="HTTPSampler.follow_redirects">true</boolProp><boolProp name="HTTPSampler.use_keepalive">true</boolProp>
<stringProp name="HTTPSampler.connect_timeout">5000</stringProp><stringProp name="HTTPSampler.response_timeout">30000</stringProp></HTTPSamplerProxy><hashTree>{extra}</hashTree>'''

hdr_json = '''<HeaderManager guiclass="HeaderPanel" testclass="HeaderManager" testname="JSON" enabled="true"><collectionProp name="HeaderManager.headers"><elementProp name="" elementType="Header"><stringProp name="Header.name">Content-Type</stringProp><stringProp name="Header.value">application/json</stringProp></elementProp></collectionProp></HeaderManager><hashTree/>'''
hdr_auth = '''<HeaderManager guiclass="HeaderPanel" testclass="HeaderManager" testname="Bearer" enabled="true"><collectionProp name="HeaderManager.headers"><elementProp name="" elementType="Header"><stringProp name="Header.name">Authorization</stringProp><stringProp name="Header.value">Bearer ${token}</stringProp></elementProp></collectionProp></HeaderManager><hashTree/>'''
extract = '''<JSONPostProcessor guiclass="JSONPostProcessorGui" testclass="JSONPostProcessor" testname="token" enabled="true"><stringProp name="JSONPostProcessor.referenceNames">token</stringProp><stringProp name="JSONPostProcessor.jsonPathExprs">$.access_token</stringProp><stringProp name="JSONPostProcessor.match_numbers">1</stringProp><stringProp name="JSONPostProcessor.defaultValues">NOTOKEN</stringProp></JSONPostProcessor><hashTree/>'''
def assert_code(code="200"):
    return f'<ResponseAssertion guiclass="AssertionGui" testclass="ResponseAssertion" testname="HTTP {code}" enabled="true"><collectionProp name="Asserion.test_strings"><stringProp name="1">{code}</stringProp></collectionProp><stringProp name="Assertion.test_field">Assertion.response_code</stringProp><boolProp name="Assertion.assume_success">false</boolProp><intProp name="Assertion.test_type">8</intProp></ResponseAssertion><hashTree/>'

body_login = '{"username":"${__P(user)}","password":"${__P(password)}"}'
A = assert_code()
steps = [
 ("GET /health", "/api/v1/health"),
 ("GET /auth/me", "/api/v1/auth/me"),
 ("GET /dashboard/summary", "/api/v1/dashboard/summary"),
 ("GET /dashboard/traffic-timeseries", "/api/v1/dashboard/traffic-timeseries"),
 ("GET /dashboard/top-talkers", "/api/v1/dashboard/top-talkers?limit=10"),
 ("GET /dashboard/findings-by-severity", "/api/v1/dashboard/findings-by-severity"),
 ("GET /findings", "/api/v1/findings?page=1&page_size=20&is_noise=false"),
 ("GET /logs", "/api/v1/logs?page=1&page_size=50"),
 ("GET /alerts/unread-count", "/api/v1/alerts/unread-count"),
]
think = '''<UniformRandomTimer guiclass="UniformRandomTimerGui" testclass="UniformRandomTimer" testname="Tiempo de pensamiento" enabled="true"><stringProp name="ConstantTimer.delay">${__P(think_ms,1000)}</stringProp><stringProp name="RandomTimer.range">${__P(think_ms,1000)}</stringProp></UniformRandomTimer><hashTree/>'''
flow = "".join(http(n, p, extra=hdr_auth + A) + "" for n, p in steps)
flow = flow.replace("</HTTPSamplerProxy><hashTree>", "</HTTPSamplerProxy><hashTree>")  # no-op, claridad

login = http("POST /auth/login", "/api/v1/auth/login", "POST", body_login, extra=hdr_json + extract + A)
mode_login_only = '${__P(login_each,false)}'
xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<jmeterTestPlan version="1.2" properties="5.0" jmeter="5.6.3"><hashTree>
<TestPlan guiclass="TestPlanGui" testclass="TestPlan" testname="NetSentinel carga" enabled="true"><boolProp name="TestPlan.functional_mode">false</boolProp><boolProp name="TestPlan.serialize_threadgroups">false</boolProp></TestPlan><hashTree>
<ThreadGroup guiclass="ThreadGroupGui" testclass="ThreadGroup" testname="Usuarios virtuales" enabled="true">
<stringProp name="ThreadGroup.on_sample_error">continue</stringProp>
<elementProp name="ThreadGroup.main_controller" elementType="LoopController"><boolProp name="LoopController.continue_forever">false</boolProp><intProp name="LoopController.loops">-1</intProp></elementProp>
<stringProp name="ThreadGroup.num_threads">${{__P(users,10)}}</stringProp><stringProp name="ThreadGroup.ramp_time">${{__P(rampup,10)}}</stringProp>
<boolProp name="ThreadGroup.scheduler">true</boolProp><stringProp name="ThreadGroup.duration">${{__P(duration,60)}}</stringProp><stringProp name="ThreadGroup.delay"></stringProp></ThreadGroup><hashTree>
<OnceOnlyController guiclass="OnceOnlyControllerGui" testclass="OnceOnlyController" testname="Login (1 vez por usuario)" enabled="true"/><hashTree>{login}</hashTree>
<TransactionController guiclass="TransactionControllerGui" testclass="TransactionController" testname="Sesion tipica: panel + hallazgos + logs" enabled="true"><boolProp name="TransactionController.parent">false</boolProp><boolProp name="TransactionController.includeTimers">false</boolProp></TransactionController><hashTree>{flow}</hashTree>
{think}
</hashTree></hashTree></hashTree></jmeterTestPlan>'''
open("plan/netsentinel.jmx", "w").write(xml)

# variante: login en cada iteracion (mide Argon2 + emision JWT)
xml2 = xml.replace('<OnceOnlyController guiclass="OnceOnlyControllerGui" testclass="OnceOnlyController" testname="Login (1 vez por usuario)" enabled="true"/><hashTree>' + login + '</hashTree>', login).replace(flow, "").replace('Sesion tipica: panel + hallazgos + logs', 'vacio')
import re
xml2 = re.sub(r'<TransactionController.*?</TransactionController><hashTree>\s*</hashTree>', '', xml2, flags=re.S)  # sin controlador vacio
open("plan/netsentinel_login.jmx", "w").write(xml2)
