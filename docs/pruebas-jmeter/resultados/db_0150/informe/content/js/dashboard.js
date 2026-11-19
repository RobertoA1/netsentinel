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

    var data = {"OkPercent": 100.0, "KoPercent": 0.0};
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
    createTable($("#apdexTable"), {"supportsControllersDiscrimination": true, "overall": {"data": [0.7117308018308188, 500, 1500, "Total"], "isController": false}, "titles": ["Apdex", "T (Toleration threshold)", "F (Frustration threshold)", "Label"], "items": [{"data": [0.9888888888888889, 500, 1500, "Busqueda de usuario (login)"], "isController": false}, {"data": [0.9814159292035398, 500, 1500, "Listado paginado de hallazgos"], "isController": false}, {"data": [0.2886297376093295, 500, 1500, "Resumen: agregados sobre firewall_logs"], "isController": false}, {"data": [0.4700460829493088, 500, 1500, "Serie temporal por hora"], "isController": false}, {"data": [0.9819168173598554, 500, 1500, "Listado paginado de logs"], "isController": false}, {"data": [0.10073260073260074, 500, 1500, "Sesion tipica: panel + hallazgos + logs"], "isController": true}, {"data": [0.9720767888307156, 500, 1500, "Hallazgos por severidad"], "isController": false}, {"data": [0.9826007326007326, 500, 1500, "Logs filtrados por origen"], "isController": false}, {"data": [0.7053291536050157, 500, 1500, "Top talkers (bytes)"], "isController": false}, {"data": [0.7728785357737105, 500, 1500, "Top puertos destino"], "isController": false}]}, function(index, item){
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
    createTable($("#statisticsTable"), {"supportsControllersDiscrimination": true, "overall": {"data": ["Total", 5353, 0, 0.0, 735.5488511115276, 0, 11550, 63.0, 2356.600000000004, 3855.4000000000015, 8854.300000000003, 59.71930920612254, 62.17277595288166, 0.0], "isController": false}, "titles": ["Label", "#Samples", "FAIL", "Error %", "Average", "Min", "Max", "Median", "90th pct", "95th pct", "99th pct", "Transactions/s", "Received", "Sent"], "items": [{"data": ["Busqueda de usuario (login)", 540, 0, 0.0, 43.514814814814805, 0, 3700, 3.0, 10.0, 23.949999999999932, 2099.230000000083, 7.128054173211717, 0.9188507332655728, 0.0], "isController": false}, {"data": ["Listado paginado de hallazgos", 565, 0, 0.0, 70.64601769911503, 0, 3955, 3.0, 11.0, 28.49999999999966, 3637.4200000000005, 6.992660800257429, 21.080413955463555, 0.0], "isController": false}, {"data": ["Resumen: agregados sobre firewall_logs", 686, 0, 0.0, 2897.2842565597703, 222, 11550, 2493.0, 5469.100000000001, 9612.8, 10658.89, 7.653175063590521, 0.568009086750859, 0.0], "isController": false}, {"data": ["Serie temporal por hora", 651, 0, 0.0, 1539.8033794162816, 91, 10028, 1154.0, 2759.6000000000004, 6527.399999999993, 9015.080000000002, 7.458838895954353, 1.1872956445708591, 0.0], "isController": false}, {"data": ["Listado paginado de logs", 553, 0, 0.0, 75.254972875226, 0, 3946, 3.0, 10.0, 27.299999999999955, 3634.4400000000005, 6.977829932745329, 24.68134767226912, 0.0], "isController": false}, {"data": ["Sesion tipica: panel + hallazgos + logs", 546, 0, 0.0, 5701.450549450543, 508, 16097, 5221.5, 13485.6, 14257.949999999999, 15304.949999999999, 6.892720983664503, 68.53376908595703, 0.0], "isController": true}, {"data": ["Hallazgos por severidad", 573, 0, 0.0, 110.30715532286227, 0, 3902, 3.0, 10.0, 139.29999999999723, 3670.0199999999995, 6.953883495145631, 0.33954509253640774, 0.0], "isController": false}, {"data": ["Logs filtrados por origen", 546, 0, 0.0, 75.78937728937728, 1, 3963, 10.0, 26.0, 44.249999999999886, 3656.159999999998, 7.034722669587064, 17.95777837724667, 0.0], "isController": false}, {"data": ["Top talkers (bytes)", 638, 0, 0.0, 654.8197492163008, 64, 2124, 586.0, 1369.5, 1522.2999999999997, 1841.15, 7.433125174759996, 2.0179773423664833, 0.0], "isController": false}, {"data": ["Top puertos destino", 601, 0, 0.0, 532.5341098169712, 41, 4649, 383.0, 1037.4000000000005, 1273.9, 4320.740000000003, 7.133277153335786, 1.1215406461787711, 0.0], "isController": false}]}, function(index, item){
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
    createTable($("#errorsTable"), {"supportsControllersDiscrimination": false, "titles": ["Type of error", "Number of errors", "% in errors", "% in all samples"], "items": []}, function(index, item){
        switch(index){
            case 2:
            case 3:
                item = item.toFixed(2) + '%';
                break;
        }
        return item;
    }, [[1, 1]]);

        // Create top5 errors by sampler
    createTable($("#top5ErrorsBySamplerTable"), {"supportsControllersDiscrimination": false, "overall": {"data": ["Total", 5353, 0, "", "", "", "", "", "", "", "", "", ""], "isController": false}, "titles": ["Sample", "#Samples", "#Errors", "Error", "#Errors", "Error", "#Errors", "Error", "#Errors", "Error", "#Errors", "Error", "#Errors"], "items": [{"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}]}, function(index, item){
        return item;
    }, [[0, 0]], 0);

});
