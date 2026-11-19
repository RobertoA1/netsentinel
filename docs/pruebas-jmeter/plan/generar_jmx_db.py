"""Genera plan/netsentinel_db.jmx: consultas SELECT (solo lectura) equivalentes a las del panel. Propiedades: users, rampup, duration, think_ms, pool, dbuser, dbpassword, dbname, dbport."""
from xml.sax.saxutils import escape as e
Q = [
 ("Resumen: agregados sobre firewall_logs", "SELECT count(*), coalesce(sum(bytes_out),0), coalesce(sum(bytes_in),0), count(DISTINCT src_ip), count(DISTINCT dst_ip) FROM firewall_logs"),
 ("Serie temporal por hora", "SELECT date_trunc('hour', ts) t, sum(bytes_out), sum(bytes_in), count(*) FROM firewall_logs GROUP BY 1 ORDER BY 1"),
 ("Top talkers (bytes)", "SELECT src_ip, sum(bytes_out) b, count(*) FROM firewall_logs GROUP BY src_ip ORDER BY b DESC LIMIT 10"),
 ("Top puertos destino", "SELECT dst_port, proto, count(*) c FROM firewall_logs GROUP BY dst_port, proto ORDER BY c DESC LIMIT 10"),
 ("Hallazgos por severidad", "SELECT severity, count(*) FROM traffic_findings WHERE is_noise = false GROUP BY severity"),
 ("Listado paginado de hallazgos", "SELECT id, finding_type, severity, score, title, src_ip, dst_ip, last_seen FROM traffic_findings WHERE is_noise = false ORDER BY last_seen DESC LIMIT 20 OFFSET 0"),
 ("Listado paginado de logs", "SELECT id, ts, src_ip, dst_ip, dst_port, proto, bytes_out FROM firewall_logs ORDER BY ts DESC LIMIT 50 OFFSET 0"),
 ("Logs filtrados por origen", "SELECT id, ts, dst_ip, dst_port FROM firewall_logs WHERE src_ip = '147.32.84.165' ORDER BY ts DESC LIMIT 50"),
 ("Busqueda de usuario (login)", "SELECT id, username, password_hash FROM users WHERE username = 'admin'"),
]
def jdbc(n, sql):
    return f'''<JDBCSampler guiclass="TestBeanGUI" testclass="JDBCSampler" testname="{e(n)}" enabled="true"><stringProp name="dataSource">pg</stringProp><stringProp name="queryType">Select Statement</stringProp><stringProp name="query">{e(sql)}</stringProp><stringProp name="queryArguments"></stringProp><stringProp name="queryArgumentsTypes"></stringProp><stringProp name="variableNames"></stringProp><stringProp name="resultVariable"></stringProp><stringProp name="queryTimeout">30</stringProp><stringProp name="resultSetHandler">Count Records</stringProp></JDBCSampler><hashTree/>'''
cfg = '''<JDBCDataSource guiclass="TestBeanGUI" testclass="JDBCDataSource" testname="PostgreSQL" enabled="true"><boolProp name="autocommit">true</boolProp><stringProp name="checkQuery">SELECT 1</stringProp><stringProp name="connectionAge">5000</stringProp><stringProp name="connectionProperties"></stringProp><stringProp name="dataSource">pg</stringProp><stringProp name="dbUrl">jdbc:postgresql://localhost:${__P(dbport,5433)}/${__P(dbname,netsentinel)}</stringProp><stringProp name="driver">org.postgresql.Driver</stringProp><stringProp name="initQuery"></stringProp><boolProp name="keepAlive">true</boolProp><stringProp name="password">${__P(dbpassword)}</stringProp><stringProp name="poolMax">${__P(pool,50)}</stringProp><stringProp name="timeout">10000</stringProp><stringProp name="transactionIsolation">DEFAULT</stringProp><stringProp name="trimInterval">60000</stringProp><stringProp name="username">${__P(dbuser)}</stringProp></JDBCDataSource><hashTree/>'''
think = '''<UniformRandomTimer guiclass="UniformRandomTimerGui" testclass="UniformRandomTimer" testname="Tiempo de pensamiento" enabled="true"><stringProp name="ConstantTimer.delay">${__P(think_ms,1000)}</stringProp><stringProp name="RandomTimer.range">${__P(think_ms,1000)}</stringProp></UniformRandomTimer><hashTree/>'''
xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<jmeterTestPlan version="1.2" properties="5.0" jmeter="5.6.3"><hashTree>
<TestPlan guiclass="TestPlanGui" testclass="TestPlan" testname="NetSentinel base de datos" enabled="true"><boolProp name="TestPlan.functional_mode">false</boolProp><boolProp name="TestPlan.serialize_threadgroups">false</boolProp></TestPlan><hashTree>{cfg}
<ThreadGroup guiclass="ThreadGroupGui" testclass="ThreadGroup" testname="Usuarios virtuales (consultas SQL)" enabled="true"><stringProp name="ThreadGroup.on_sample_error">continue</stringProp>
<elementProp name="ThreadGroup.main_controller" elementType="LoopController"><boolProp name="LoopController.continue_forever">false</boolProp><intProp name="LoopController.loops">-1</intProp></elementProp>
<stringProp name="ThreadGroup.num_threads">${{__P(users,10)}}</stringProp><stringProp name="ThreadGroup.ramp_time">${{__P(rampup,10)}}</stringProp><boolProp name="ThreadGroup.scheduler">true</boolProp><stringProp name="ThreadGroup.duration">${{__P(duration,60)}}</stringProp><stringProp name="ThreadGroup.delay"></stringProp></ThreadGroup><hashTree>
<TransactionController guiclass="TransactionControllerGui" testclass="TransactionController" testname="Sesion tipica: panel + hallazgos + logs" enabled="true"><boolProp name="TransactionController.parent">false</boolProp><boolProp name="TransactionController.includeTimers">false</boolProp></TransactionController><hashTree>{"".join(jdbc(n,s) for n,s in Q)}</hashTree>{think}
</hashTree></hashTree></hashTree></jmeterTestPlan>'''
open("plan/netsentinel_db.jmx", "w").write(xml)
