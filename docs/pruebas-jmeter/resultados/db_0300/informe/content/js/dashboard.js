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

    var data = {"OkPercent": 99.91953329309997, "KoPercent": 0.08046670690002011};
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
    createTable($("#apdexTable"), {"supportsControllersDiscrimination": true, "overall": {"data": [0.22647762842938685, 500, 1500, "Total"], "isController": false}, "titles": ["Apdex", "T (Toleration threshold)", "F (Frustration threshold)", "Label"], "items": [{"data": [0.3611111111111111, 500, 1500, "Busqueda de usuario (login)"], "isController": false}, {"data": [0.40091743119266054, 500, 1500, "Listado paginado de hallazgos"], "isController": false}, {"data": [0.037642045454545456, 500, 1500, "Resumen: agregados sobre firewall_logs"], "isController": false}, {"data": [0.03577371048252912, 500, 1500, "Serie temporal por hora"], "isController": false}, {"data": [0.424901185770751, 500, 1500, "Listado paginado de logs"], "isController": false}, {"data": [0.0, 500, 1500, "Sesion tipica: panel + hallazgos + logs"], "isController": true}, {"data": [0.3996415770609319, 500, 1500, "Hallazgos por severidad"], "isController": false}, {"data": [0.46284501061571126, 500, 1500, "Logs filtrados por origen"], "isController": false}, {"data": [0.078125, 500, 1500, "Top talkers (bytes)"], "isController": false}, {"data": [0.17857142857142858, 500, 1500, "Top puertos destino"], "isController": false}]}, function(index, item){
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
    createTable($("#statisticsTable"), {"supportsControllersDiscrimination": true, "overall": {"data": ["Total", 4971, 4, 0.08046670690002011, 3406.9597666465506, 0, 16732, 2537.0, 8306.2, 9664.999999999995, 13499.799999999985, 52.70579753170194, 54.18119216583082, 0.0], "isController": false}, "titles": ["Label", "#Samples", "FAIL", "Error %", "Average", "Min", "Max", "Median", "90th pct", "95th pct", "99th pct", "Transactions/s", "Received", "Sent"], "items": [{"data": ["Busqueda de usuario (login)", 450, 1, 0.2222222222222222, 2060.5644444444447, 0, 10001, 1900.0, 4260.50000000001, 7174.899999999993, 9096.9, 6.053675926548732, 0.7798837189749109, 0.0], "isController": false}, {"data": ["Listado paginado de hallazgos", 545, 0, 0.0, 1627.8495412844038, 0, 9108, 1094.0, 3462.8, 4387.099999999991, 8795.359999999995, 6.534928895177343, 19.70051318301998, 0.0], "isController": false}, {"data": ["Resumen: agregados sobre firewall_logs", 704, 1, 0.14204545454545456, 7547.715909090903, 391, 16732, 7706.0, 12153.5, 14173.5, 15535.900000000001, 7.464269052970864, 0.5541958018787905, 0.0], "isController": false}, {"data": ["Serie temporal por hora", 601, 0, 0.0, 5728.412645590684, 273, 12895, 5533.0, 9820.80000000001, 11737.7, 12640.64, 6.56242493066323, 1.0446047497051822, 0.0], "isController": false}, {"data": ["Listado paginado de logs", 506, 0, 0.0, 1804.820158102768, 0, 9229, 1094.0, 4340.000000000001, 6042.449999999997, 9117.37, 6.232141097645088, 22.043764702803234, 0.0], "isController": false}, {"data": ["Sesion tipica: panel + hallazgos + logs", 460, 3, 0.6521739130434783, 28650.706521739114, 10372, 43439, 30653.0, 36530.600000000006, 38245.95, 41611.869999999995, 5.747988204128555, 57.11185899388339, 0.0], "isController": true}, {"data": ["Hallazgos por severidad", 558, 0, 0.0, 1635.7437275985662, 0, 8899, 1237.5, 3435.1000000000004, 4096.15, 8558.829999999994, 6.935209237002697, 0.3386332635255223, 0.0], "isController": false}, {"data": ["Logs filtrados por origen", 471, 1, 0.21231422505307856, 1929.4246284501062, 1, 10001, 891.0, 5649.800000000001, 8505.399999999998, 9090.039999999997, 5.996333452156644, 15.275741027779192, 0.0], "isController": false}, {"data": ["Top talkers (bytes)", 576, 0, 0.0, 3496.2274305555557, 65, 11154, 3423.0, 5581.100000000001, 6269.799999999999, 10305.040000000003, 6.443817962142569, 1.749395892066049, 0.0], "isController": false}, {"data": ["Top puertos destino", 560, 1, 0.17857142857142858, 2886.833928571426, 47, 10854, 2672.0, 5013.8, 5478.449999999999, 10210.759999999997, 6.743088334457181, 1.0594282636246508, 0.0], "isController": false}]}, function(index, item){
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
    createTable($("#errorsTable"), {"supportsControllersDiscrimination": false, "titles": ["Type of error", "Number of errors", "% in errors", "% in all samples"], "items": [{"data": ["null 0/java.sql.SQLException: Cannot get a connection, pool error Timeout waiting for idle object, borrowMaxWaitDuration=PT10S", 4, 100.0, 0.08046670690002011], "isController": false}]}, function(index, item){
        switch(index){
            case 2:
            case 3:
                item = item.toFixed(2) + '%';
                break;
        }
        return item;
    }, [[1, 1]]);

        // Create top5 errors by sampler
    createTable($("#top5ErrorsBySamplerTable"), {"supportsControllersDiscrimination": false, "overall": {"data": ["Total", 4971, 4, "null 0/java.sql.SQLException: Cannot get a connection, pool error Timeout waiting for idle object, borrowMaxWaitDuration=PT10S", 4, "", "", "", "", "", "", "", ""], "isController": false}, "titles": ["Sample", "#Samples", "#Errors", "Error", "#Errors", "Error", "#Errors", "Error", "#Errors", "Error", "#Errors", "Error", "#Errors"], "items": [{"data": ["Busqueda de usuario (login)", 450, 1, "null 0/java.sql.SQLException: Cannot get a connection, pool error Timeout waiting for idle object, borrowMaxWaitDuration=PT10S", 1, "", "", "", "", "", "", "", ""], "isController": false}, {"data": [], "isController": false}, {"data": ["Resumen: agregados sobre firewall_logs", 704, 1, "null 0/java.sql.SQLException: Cannot get a connection, pool error Timeout waiting for idle object, borrowMaxWaitDuration=PT10S", 1, "", "", "", "", "", "", "", ""], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": ["Logs filtrados por origen", 471, 1, "null 0/java.sql.SQLException: Cannot get a connection, pool error Timeout waiting for idle object, borrowMaxWaitDuration=PT10S", 1, "", "", "", "", "", "", "", ""], "isController": false}, {"data": [], "isController": false}, {"data": ["Top puertos destino", 560, 1, "null 0/java.sql.SQLException: Cannot get a connection, pool error Timeout waiting for idle object, borrowMaxWaitDuration=PT10S", 1, "", "", "", "", "", "", "", ""], "isController": false}]}, function(index, item){
        return item;
    }, [[0, 0]], 0);

});
