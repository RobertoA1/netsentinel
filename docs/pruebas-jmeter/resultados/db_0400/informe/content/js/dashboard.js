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

    var data = {"OkPercent": 96.28482972136223, "KoPercent": 3.7151702786377707};
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
    createTable($("#apdexTable"), {"supportsControllersDiscrimination": true, "overall": {"data": [0.20743565300285988, 500, 1500, "Total"], "isController": false}, "titles": ["Apdex", "T (Toleration threshold)", "F (Frustration threshold)", "Label"], "items": [{"data": [0.4298245614035088, 500, 1500, "Busqueda de usuario (login)"], "isController": false}, {"data": [0.5190476190476191, 500, 1500, "Listado paginado de hallazgos"], "isController": false}, {"data": [0.024111675126903553, 500, 1500, "Resumen: agregados sobre firewall_logs"], "isController": false}, {"data": [0.008356545961002786, 500, 1500, "Serie temporal por hora"], "isController": false}, {"data": [0.5446650124069479, 500, 1500, "Listado paginado de logs"], "isController": false}, {"data": [0.0, 500, 1500, "Sesion tipica: panel + hallazgos + logs"], "isController": true}, {"data": [0.3903966597077244, 500, 1500, "Hallazgos por severidad"], "isController": false}, {"data": [0.5025, 500, 1500, "Logs filtrados por origen"], "isController": false}, {"data": [0.01303680981595092, 500, 1500, "Top talkers (bytes)"], "isController": false}, {"data": [0.09812286689419795, 500, 1500, "Top puertos destino"], "isController": false}]}, function(index, item){
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
    createTable($("#statisticsTable"), {"supportsControllersDiscrimination": true, "overall": {"data": ["Total", 4845, 180, 3.7151702786377707, 5319.743446852431, 0, 20835, 5127.0, 10675.400000000012, 12459.59999999999, 18166.08, 50.55405997620986, 43.377959013517604, 0.0], "isController": false}, "titles": ["Label", "#Samples", "FAIL", "Error %", "Average", "Min", "Max", "Median", "90th pct", "95th pct", "99th pct", "Transactions/s", "Received", "Sent"], "items": [{"data": ["Busqueda de usuario (login)", 399, 2, 0.5012531328320802, 2636.53634085213, 0, 10001, 3311.0, 5530.0, 5653.0, 8295.0, 8.46504720483717, 1.0897057653548319, 0.0], "isController": false}, {"data": ["Listado paginado de hallazgos", 420, 12, 2.857142857142857, 2162.388095238095, 1, 10002, 781.5, 7633.000000000005, 9762.55, 10000.79, 5.771688493726724, 16.917939816405337, 0.0], "isController": false}, {"data": ["Resumen: agregados sobre firewall_logs", 788, 12, 1.5228426395939085, 8421.406091370558, 707, 19135, 8545.0, 13344.6, 14690.549999999997, 18003.370000000006, 8.222208309856216, 0.6126875560842255, 0.0], "isController": false}, {"data": ["Serie temporal por hora", 718, 35, 4.874651810584958, 9335.72562674094, 586, 20835, 8294.5, 16240.900000000001, 18238.4, 19689.389999999992, 7.6904950622308865, 1.199642001697693, 0.0], "isController": false}, {"data": ["Listado paginado de logs", 403, 4, 0.9925558312655087, 1916.9454094292807, 1, 10001, 394.0, 4975.6, 5691.399999999998, 9993.919999999996, 6.492983388918427, 22.744480007491905, 0.0], "isController": false}, {"data": ["Sesion tipica: panel + hallazgos + logs", 400, 157, 39.25, 42594.77000000002, 32843, 61822, 39964.0, 53214.6, 55637.3, 59558.13000000001, 5.065663665260945, 49.51176698263744, 0.0], "isController": true}, {"data": ["Hallazgos por severidad", 479, 22, 4.592901878914405, 2972.2421711899806, 1, 10015, 1710.0, 8687.0, 10000.0, 10001.4, 5.904905139363158, 0.30050855070945154, 0.0], "isController": false}, {"data": ["Logs filtrados por origen", 400, 5, 1.25, 2142.0325, 6, 10020, 940.5, 5298.500000000001, 5500.85, 10000.99, 7.613681786169747, 19.201683159011743, 0.0], "isController": false}, {"data": ["Top talkers (bytes)", 652, 38, 5.828220858895706, 6508.188650306746, 473, 12081, 6595.5, 10001.0, 11048.35, 11679.86, 7.187661915313468, 1.8768826961448997, 0.0], "isController": false}, {"data": ["Top puertos destino", 586, 50, 8.532423208191126, 5424.013651877135, 164, 11816, 5836.5, 10000.0, 10001.0, 10935.95, 6.722110696874103, 1.0204868081445368, 0.0], "isController": false}]}, function(index, item){
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
    createTable($("#errorsTable"), {"supportsControllersDiscrimination": false, "titles": ["Type of error", "Number of errors", "% in errors", "% in all samples"], "items": [{"data": ["null 0/java.sql.SQLException: Cannot get a connection, pool error Timeout waiting for idle object, borrowMaxWaitDuration=PT10S", 180, 100.0, 3.7151702786377707], "isController": false}]}, function(index, item){
        switch(index){
            case 2:
            case 3:
                item = item.toFixed(2) + '%';
                break;
        }
        return item;
    }, [[1, 1]]);

        // Create top5 errors by sampler
    createTable($("#top5ErrorsBySamplerTable"), {"supportsControllersDiscrimination": false, "overall": {"data": ["Total", 4845, 180, "null 0/java.sql.SQLException: Cannot get a connection, pool error Timeout waiting for idle object, borrowMaxWaitDuration=PT10S", 180, "", "", "", "", "", "", "", ""], "isController": false}, "titles": ["Sample", "#Samples", "#Errors", "Error", "#Errors", "Error", "#Errors", "Error", "#Errors", "Error", "#Errors", "Error", "#Errors"], "items": [{"data": ["Busqueda de usuario (login)", 399, 2, "null 0/java.sql.SQLException: Cannot get a connection, pool error Timeout waiting for idle object, borrowMaxWaitDuration=PT10S", 2, "", "", "", "", "", "", "", ""], "isController": false}, {"data": ["Listado paginado de hallazgos", 420, 12, "null 0/java.sql.SQLException: Cannot get a connection, pool error Timeout waiting for idle object, borrowMaxWaitDuration=PT10S", 12, "", "", "", "", "", "", "", ""], "isController": false}, {"data": ["Resumen: agregados sobre firewall_logs", 788, 12, "null 0/java.sql.SQLException: Cannot get a connection, pool error Timeout waiting for idle object, borrowMaxWaitDuration=PT10S", 12, "", "", "", "", "", "", "", ""], "isController": false}, {"data": ["Serie temporal por hora", 718, 35, "null 0/java.sql.SQLException: Cannot get a connection, pool error Timeout waiting for idle object, borrowMaxWaitDuration=PT10S", 35, "", "", "", "", "", "", "", ""], "isController": false}, {"data": ["Listado paginado de logs", 403, 4, "null 0/java.sql.SQLException: Cannot get a connection, pool error Timeout waiting for idle object, borrowMaxWaitDuration=PT10S", 4, "", "", "", "", "", "", "", ""], "isController": false}, {"data": [], "isController": false}, {"data": ["Hallazgos por severidad", 479, 22, "null 0/java.sql.SQLException: Cannot get a connection, pool error Timeout waiting for idle object, borrowMaxWaitDuration=PT10S", 22, "", "", "", "", "", "", "", ""], "isController": false}, {"data": ["Logs filtrados por origen", 400, 5, "null 0/java.sql.SQLException: Cannot get a connection, pool error Timeout waiting for idle object, borrowMaxWaitDuration=PT10S", 5, "", "", "", "", "", "", "", ""], "isController": false}, {"data": ["Top talkers (bytes)", 652, 38, "null 0/java.sql.SQLException: Cannot get a connection, pool error Timeout waiting for idle object, borrowMaxWaitDuration=PT10S", 38, "", "", "", "", "", "", "", ""], "isController": false}, {"data": ["Top puertos destino", 586, 50, "null 0/java.sql.SQLException: Cannot get a connection, pool error Timeout waiting for idle object, borrowMaxWaitDuration=PT10S", 50, "", "", "", "", "", "", "", ""], "isController": false}]}, function(index, item){
        return item;
    }, [[0, 0]], 0);

});
