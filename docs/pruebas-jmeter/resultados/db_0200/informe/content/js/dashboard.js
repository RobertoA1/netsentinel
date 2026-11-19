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
    createTable($("#apdexTable"), {"supportsControllersDiscrimination": true, "overall": {"data": [0.4929072096128171, 500, 1500, "Total"], "isController": false}, "titles": ["Apdex", "T (Toleration threshold)", "F (Frustration threshold)", "Label"], "items": [{"data": [0.86, 500, 1500, "Busqueda de usuario (login)"], "isController": false}, {"data": [0.8924914675767918, 500, 1500, "Listado paginado de hallazgos"], "isController": false}, {"data": [0.0425531914893617, 500, 1500, "Resumen: agregados sobre firewall_logs"], "isController": false}, {"data": [0.08987915407854985, 500, 1500, "Serie temporal por hora"], "isController": false}, {"data": [0.8964601769911504, 500, 1500, "Listado paginado de logs"], "isController": false}, {"data": [0.0, 500, 1500, "Sesion tipica: panel + hallazgos + logs"], "isController": true}, {"data": [0.8770764119601329, 500, 1500, "Hallazgos por severidad"], "isController": false}, {"data": [0.8786764705882353, 500, 1500, "Logs filtrados por origen"], "isController": false}, {"data": [0.247244094488189, 500, 1500, "Top talkers (bytes)"], "isController": false}, {"data": [0.3525641025641026, 500, 1500, "Top puertos destino"], "isController": false}]}, function(index, item){
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
    createTable($("#statisticsTable"), {"supportsControllersDiscrimination": true, "overall": {"data": ["Total", 5448, 0, 0.0, 1431.6971365638747, 0, 9652, 816.0, 4044.0, 5379.600000000002, 7530.690000000004, 60.55015282022784, 63.117662892470136, 0.0], "isController": false}, "titles": ["Label", "#Samples", "FAIL", "Error %", "Average", "Min", "Max", "Median", "90th pct", "95th pct", "99th pct", "Transactions/s", "Received", "Sent"], "items": [{"data": ["Busqueda de usuario (login)", 525, 0, 0.0, 300.45523809523826, 0, 3213, 9.0, 950.4000000000001, 1495.6, 2119.2000000000003, 7.057779689726561, 0.9097919131288146, 0.0], "isController": false}, {"data": ["Listado paginado de hallazgos", 586, 0, 0.0, 226.16894197952237, 1, 2299, 9.0, 845.1000000000005, 1148.4999999999993, 1789.6899999999996, 7.415562557736355, 22.355314077863408, 0.0], "isController": false}, {"data": ["Resumen: agregados sobre firewall_logs", 705, 0, 0.0, 4672.107801418441, 539, 9652, 4801.0, 7250.399999999999, 7909.499999999998, 8667.059999999994, 7.83550986385107, 0.5815417477076966, 0.0], "isController": false}, {"data": ["Serie temporal por hora", 662, 0, 0.0, 2677.273413897282, 234, 5671, 2633.5, 4158.700000000002, 4614.8, 5439.11, 7.616198803497469, 1.212344145478601, 0.0], "isController": false}, {"data": ["Listado paginado de logs", 565, 0, 0.0, 230.92389380530938, 1, 2201, 9.0, 812.8000000000002, 1218.3999999999999, 1936.38, 7.297101823629695, 25.81064727069019, 0.0], "isController": false}, {"data": ["Sesion tipica: panel + hallazgos + logs", 544, 0, 0.0, 11912.764705882355, 2570, 18152, 12161.0, 14770.0, 15291.5, 17036.89999999999, 6.89392979343556, 68.52451566658219, 0.0], "isController": true}, {"data": ["Hallazgos por severidad", 602, 0, 0.0, 273.4302325581398, 1, 3427, 9.0, 987.2000000000003, 1377.5500000000002, 2192.0800000000017, 7.495579849092312, 0.3659951098189606, 0.0], "isController": false}, {"data": ["Logs filtrados por origen", 544, 0, 0.0, 274.045955882353, 4, 4117, 23.5, 935.5, 1280.25, 2095.899999999999, 7.156105710414502, 18.26763703810889, 0.0], "isController": false}, {"data": ["Top talkers (bytes)", 635, 0, 0.0, 1771.3527559055121, 204, 4501, 1644.0, 2975.1999999999994, 3517.7999999999993, 4305.32, 7.47612936647162, 2.029652308475694, 0.0], "isController": false}, {"data": ["Top puertos destino", 624, 0, 0.0, 1401.3685897435882, 225, 4268, 1229.5, 2529.0, 2850.25, 3532.0, 7.466704957461321, 1.1739643536633522, 0.0], "isController": false}]}, function(index, item){
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
    createTable($("#top5ErrorsBySamplerTable"), {"supportsControllersDiscrimination": false, "overall": {"data": ["Total", 5448, 0, "", "", "", "", "", "", "", "", "", ""], "isController": false}, "titles": ["Sample", "#Samples", "#Errors", "Error", "#Errors", "Error", "#Errors", "Error", "#Errors", "Error", "#Errors", "Error", "#Errors"], "items": [{"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}]}, function(index, item){
        return item;
    }, [[0, 0]], 0);

});
