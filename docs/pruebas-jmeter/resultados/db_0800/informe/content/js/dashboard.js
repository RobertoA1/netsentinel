/*
   Licensed to the Apache Software Foundation (ASF) under one or more
   contributor license agreements.  See the NOTICE file distributed with
   this work for additional information regarding copyright ownership.
   The ASF licenses this file to You under the Apache License, Version 2.0
   (the "License"); you may not use this file except in compliance with
   the License.  You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
*/
var showControllersOnly = false;
var seriesFilter = "";
var filtersOnlySampleSeries = true;

/*
 * Add header in statistics table to group metrics by category
 * format
 *
 */
function summaryTableHeader(header) {
    var newRow = header.insertRow(-1);
    newRow.className = "tablesorter-no-sort";
    var cell = document.createElement('th');
    cell.setAttribute("data-sorter", false);
    cell.colSpan = 1;
    cell.innerHTML = "Requests";
    newRow.appendChild(cell);

    cell = document.createElement('th');
    cell.setAttribute("data-sorter", false);
    cell.colSpan = 3;
    cell.innerHTML = "Executions";
    newRow.appendChild(cell);

    cell = document.createElement('th');
    cell.setAttribute("data-sorter", false);
    cell.colSpan = 7;
    cell.innerHTML = "Response Times (ms)";
    newRow.appendChild(cell);

    cell = document.createElement('th');
    cell.setAttribute("data-sorter", false);
    cell.colSpan = 1;
    cell.innerHTML = "Throughput";
    newRow.appendChild(cell);

    cell = document.createElement('th');
    cell.setAttribute("data-sorter", false);
    cell.colSpan = 2;
    cell.innerHTML = "Network (KB/sec)";
    newRow.appendChild(cell);
}

/*
 * Populates the table identified by id parameter with the specified data and
 * format
 *
 */
function createTable(table, info, formatter, defaultSorts, seriesIndex, headerCreator) {
    var tableRef = table[0];

    // Create header and populate it with data.titles array
    var header = tableRef.createTHead();

    // Call callback is available
    if(headerCreator) {
        headerCreator(header);
    }

    var newRow = header.insertRow(-1);
    for (var index = 0; index < info.titles.length; index++) {
        var cell = document.createElement('th');
        cell.innerHTML = info.titles[index];
        newRow.appendChild(cell);
    }

    var tBody;

    // Create overall body if defined
    if(info.overall){
        tBody = document.createElement('tbody');
        tBody.className = "tablesorter-no-sort";
        tableRef.appendChild(tBody);
        var newRow = tBody.insertRow(-1);
        var data = info.overall.data;
        for(var index=0;index < data.length; index++){
            var cell = newRow.insertCell(-1);
            cell.innerHTML = formatter ? formatter(index, data[index]): data[index];
        }
    }

    // Create regular body
    tBody = document.createElement('tbody');
    tableRef.appendChild(tBody);

    var regexp;
    if(seriesFilter) {
        regexp = new RegExp(seriesFilter, 'i');
    }
    // Populate body with data.items array
    for(var index=0; index < info.items.length; index++){
        var item = info.items[index];
        if((!regexp || filtersOnlySampleSeries && !info.supportsControllersDiscrimination || regexp.test(item.data[seriesIndex]))
                &&
                (!showControllersOnly || !info.supportsControllersDiscrimination || item.isController)){
            if(item.data.length > 0) {
                var newRow = tBody.insertRow(-1);
                for(var col=0; col < item.data.length; col++){
                    var cell = newRow.insertCell(-1);
                    cell.innerHTML = formatter ? formatter(col, item.data[col]) : item.data[col];
                }
            }
        }
    }

    // Add support of columns sort
    table.tablesorter({sortList : defaultSorts});
}

$(document).ready(function() {

    // Customize table sorter default options
    $.extend( $.tablesorter.defaults, {
        theme: 'blue',
        cssInfoBlock: "tablesorter-no-sort",
        widthFixed: true,
        widgets: ['zebra']
    });

    var data = {"OkPercent": 78.80935506732814, "KoPercent": 21.190644932671862};
    var dataset = [
        {
            "label" : "FAIL",
            "data" : data.KoPercent,
            "color" : "#FF6347"
        },
        {
            "label" : "PASS",
            "data" : data.OkPercent,
            "color" : "#9ACD32"
        }];
    $.plot($("#flot-requests-summary"), dataset, {
        series : {
            pie : {
                show : true,
                radius : 1,
                label : {
                    show : true,
                    radius : 3 / 4,
                    formatter : function(label, series) {
                        return '<div style="font-size:8pt;text-align:center;padding:2px;color:white;">'
                            + label
                            + '<br/>'
                            + Math.round10(series.percent, -2)
                            + '%</div>';
                    },
                    background : {
                        opacity : 0.5,
                        color : '#000'
                    }
                }
            }
        },
        legend : {
            show : true
        }
    });

    // Creates APDEX table
    createTable($("#apdexTable"), {"supportsControllersDiscrimination": true, "overall": {"data": [0.2767404209390178, 500, 1500, "Total"], "isController": false}, "titles": ["Apdex", "T (Toleration threshold)", "F (Frustration threshold)", "Label"], "items": [{"data": [0.40326633165829145, 500, 1500, "Busqueda de usuario (login)"], "isController": false}, {"data": [0.736875, 500, 1500, "Listado paginado de hallazgos"], "isController": false}, {"data": [0.01423841059602649, 500, 1500, "Resumen: agregados sobre firewall_logs"], "isController": false}, {"data": [0.0024469820554649264, 500, 1500, "Serie temporal por hora"], "isController": false}, {"data": [0.8925, 500, 1500, "Listado paginado de logs"], "isController": false}, {"data": [0.0, 500, 1500, "Sesion tipica: panel + hallazgos + logs"], "isController": true}, {"data": [0.3424657534246575, 500, 1500, "Hallazgos por severidad"], "isController": false}, {"data": [0.775, 500, 1500, "Logs filtrados por origen"], "isController": false}, {"data": [0.0060373216245883645, 500, 1500, "Top talkers (bytes)"], "isController": false}, {"data": [0.01768292682926829, 500, 1500, "Top puertos destino"], "isController": false}]}, function(index, item){
        switch(index){
            case 0:
                item = item.toFixed(3);
                break;
            case 1:
            case 2:
                item = formatDuration(item);
                break;
        }
        return item;
    }, [[0, 0]], 3);

    // Create statistics table
    createTable($("#statisticsTable"), {"supportsControllersDiscrimination": true, "overall": {"data": ["Total", 8466, 1794, 21.190644932671862, 6480.399362154522, 0, 18756, 8778.5, 12023.900000000001, 13276.65, 16481.33, 84.27402496565729, 78.87032663837127, 0.0], "isController": false}, "titles": ["Label", "#Samples", "FAIL", "Error %", "Average", "Min", "Max", "Median", "90th pct", "95th pct", "99th pct", "Transactions/s", "Received", "Sent"], "items": [{"data": ["Busqueda de usuario (login)", 796, 171, 21.482412060301506, 4861.79773869347, 0, 10024, 4732.0, 10001.0, 10001.0, 10007.03, 21.90423775454045, 2.6581633530544853, 0.0], "isController": false}, {"data": ["Listado paginado de hallazgos", 800, 3, 0.375, 1101.65, 0, 10001, 1.0, 4535.5, 5907.799999999999, 9470.58, 34.73579089053884, 104.33572379347402, 0.0], "isController": false}, {"data": ["Resumen: agregados sobre firewall_logs", 1510, 686, 45.43046357615894, 10533.497350993372, 179, 18756, 10001.0, 15892.0, 16530.45, 17835.80000000001, 15.031157299567978, 1.2489672300862051, 0.0], "isController": false}, {"data": ["Serie temporal por hora", 1226, 612, 49.9184339314845, 10858.313213703097, 170, 14733, 10002.0, 13021.6, 13339.0, 13889.060000000001, 12.59994655813858, 1.5941227120203079, 0.0], "isController": false}, {"data": ["Listado paginado de logs", 800, 2, 0.25, 406.4474999999998, 0, 10001, 1.0, 1323.8999999999965, 3274.899999999994, 7242.550000000001, 24.423752098916193, 86.1792331323462, 0.0], "isController": false}, {"data": ["Sesion tipica: panel + hallazgos + logs", 799, 715, 89.48685857321652, 51816.38297872337, 35684, 74397, 51339.0, 60095.0, 63070.0, 67363.0, 9.303029597373262, 90.56123678844632, 0.0], "isController": true}, {"data": ["Hallazgos por severidad", 803, 6, 0.7471980074719801, 3446.660024906597, 0, 10008, 2685.0, 9380.6, 9529.0, 9984.560000000001, 12.176629363418556, 0.5986491314863677, 0.0], "isController": false}, {"data": ["Logs filtrados por origen", 800, 39, 4.875, 1577.3499999999992, 0, 10039, 5.0, 9437.4, 10000.0, 10004.98, 23.939910823832182, 58.24242479501451, 0.0], "isController": false}, {"data": ["Top talkers (bytes)", 911, 213, 23.380900109769485, 10551.455543358952, 258, 12648, 10841.0, 11768.800000000001, 11982.4, 12354.92, 9.836419586460078, 2.261672987636992, 0.0], "isController": false}, {"data": ["Top puertos destino", 820, 62, 7.560975609756097, 8447.310975609755, 44, 11745, 9336.5, 11003.9, 11223.3, 11577.58, 10.457849764060708, 1.5940598695957149, 0.0], "isController": false}]}, function(index, item){
        switch(index){
            // Errors pct
            case 3:
                item = item.toFixed(2) + '%';
                break;
            // Mean
            case 4:
            // Mean
            case 7:
            // Median
            case 8:
            // Percentile 1
            case 9:
            // Percentile 2
            case 10:
            // Percentile 3
            case 11:
            // Throughput
            case 12:
            // Kbytes/s
            case 13:
            // Sent Kbytes/s
                item = item.toFixed(2);
                break;
        }
        return item;
    }, [[0, 0]], 0, summaryTableHeader);

    // Create error table
    createTable($("#errorsTable"), {"supportsControllersDiscrimination": false, "titles": ["Type of error", "Number of errors", "% in errors", "% in all samples"], "items": [{"data": ["null 0/java.sql.SQLException: Cannot get a connection, pool error Timeout waiting for idle object, borrowMaxWaitDuration=PT10S", 1794, 100.0, 21.190644932671862], "isController": false}]}, function(index, item){
        switch(index){
            case 2:
            case 3:
                item = item.toFixed(2) + '%';
                break;
        }
        return item;
    }, [[1, 1]]);

        // Create top5 errors by sampler
    createTable($("#top5ErrorsBySamplerTable"), {"supportsControllersDiscrimination": false, "overall": {"data": ["Total", 8466, 1794, "null 0/java.sql.SQLException: Cannot get a connection, pool error Timeout waiting for idle object, borrowMaxWaitDuration=PT10S", 1794, "", "", "", "", "", "", "", ""], "isController": false}, "titles": ["Sample", "#Samples", "#Errors", "Error", "#Errors", "Error", "#Errors", "Error", "#Errors", "Error", "#Errors", "Error", "#Errors"], "items": [{"data": ["Busqueda de usuario (login)", 796, 171, "null 0/java.sql.SQLException: Cannot get a connection, pool error Timeout waiting for idle object, borrowMaxWaitDuration=PT10S", 171, "", "", "", "", "", "", "", ""], "isController": false}, {"data": ["Listado paginado de hallazgos", 800, 3, "null 0/java.sql.SQLException: Cannot get a connection, pool error Timeout waiting for idle object, borrowMaxWaitDuration=PT10S", 3, "", "", "", "", "", "", "", ""], "isController": false}, {"data": ["Resumen: agregados sobre firewall_logs", 1510, 686, "null 0/java.sql.SQLException: Cannot get a connection, pool error Timeout waiting for idle object, borrowMaxWaitDuration=PT10S", 686, "", "", "", "", "", "", "", ""], "isController": false}, {"data": ["Serie temporal por hora", 1226, 612, "null 0/java.sql.SQLException: Cannot get a connection, pool error Timeout waiting for idle object, borrowMaxWaitDuration=PT10S", 612, "", "", "", "", "", "", "", ""], "isController": false}, {"data": ["Listado paginado de logs", 800, 2, "null 0/java.sql.SQLException: Cannot get a connection, pool error Timeout waiting for idle object, borrowMaxWaitDuration=PT10S", 2, "", "", "", "", "", "", "", ""], "isController": false}, {"data": [], "isController": false}, {"data": ["Hallazgos por severidad", 803, 6, "null 0/java.sql.SQLException: Cannot get a connection, pool error Timeout waiting for idle object, borrowMaxWaitDuration=PT10S", 6, "", "", "", "", "", "", "", ""], "isController": false}, {"data": ["Logs filtrados por origen", 800, 39, "null 0/java.sql.SQLException: Cannot get a connection, pool error Timeout waiting for idle object, borrowMaxWaitDuration=PT10S", 39, "", "", "", "", "", "", "", ""], "isController": false}, {"data": ["Top talkers (bytes)", 911, 213, "null 0/java.sql.SQLException: Cannot get a connection, pool error Timeout waiting for idle object, borrowMaxWaitDuration=PT10S", 213, "", "", "", "", "", "", "", ""], "isController": false}, {"data": ["Top puertos destino", 820, 62, "null 0/java.sql.SQLException: Cannot get a connection, pool error Timeout waiting for idle object, borrowMaxWaitDuration=PT10S", 62, "", "", "", "", "", "", "", ""], "isController": false}]}, function(index, item){
        return item;
    }, [[0, 0]], 0);

});
