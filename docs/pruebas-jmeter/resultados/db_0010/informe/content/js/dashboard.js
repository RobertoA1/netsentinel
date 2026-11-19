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
    createTable($("#apdexTable"), {"supportsControllersDiscrimination": true, "overall": {"data": [0.9982876712328768, 500, 1500, "Total"], "isController": false}, "titles": ["Apdex", "T (Toleration threshold)", "F (Frustration threshold)", "Label"], "items": [{"data": [1.0, 500, 1500, "Busqueda de usuario (login)"], "isController": false}, {"data": [1.0, 500, 1500, "Listado paginado de hallazgos"], "isController": false}, {"data": [0.9920634920634921, 500, 1500, "Resumen: agregados sobre firewall_logs"], "isController": false}, {"data": [1.0, 500, 1500, "Serie temporal por hora"], "isController": false}, {"data": [1.0, 500, 1500, "Listado paginado de logs"], "isController": false}, {"data": [0.990909090909091, 500, 1500, "Sesion tipica: panel + hallazgos + logs"], "isController": true}, {"data": [1.0, 500, 1500, "Hallazgos por severidad"], "isController": false}, {"data": [1.0, 500, 1500, "Logs filtrados por origen"], "isController": false}, {"data": [1.0, 500, 1500, "Top talkers (bytes)"], "isController": false}, {"data": [1.0, 500, 1500, "Top puertos destino"], "isController": false}]}, function(index, item){
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
    createTable($("#statisticsTable"), {"supportsControllersDiscrimination": true, "overall": {"data": ["Total", 529, 0, 0.0, 39.53497164461249, 0, 929, 2.0, 159.0, 165.0, 182.70000000000005, 5.997800428576287, 6.430526600358281, 0.0], "isController": false}, "titles": ["Label", "#Samples", "FAIL", "Error %", "Average", "Min", "Max", "Median", "90th pct", "95th pct", "99th pct", "Transactions/s", "Received", "Sent"], "items": [{"data": ["Busqueda de usuario (login)", 53, 0, 0.0, 0.7547169811320755, 0, 2, 1.0, 1.0, 1.0, 2.0, 0.7136317121775193, 0.09199158789788334, 0.0], "isController": false}, {"data": ["Listado paginado de hallazgos", 58, 0, 0.0, 1.0689655172413797, 0, 3, 1.0, 2.0, 2.0, 3.0, 0.7207744597298338, 2.1728815988144503, 0.0], "isController": false}, {"data": ["Resumen: agregados sobre firewall_logs", 63, 0, 0.0, 178.33333333333331, 155, 929, 163.0, 181.6, 191.2, 929.0, 0.7260406582768635, 0.05388583010648596, 0.0], "isController": false}, {"data": ["Serie temporal por hora", 62, 0, 0.0, 66.56451612903227, 61, 113, 65.0, 70.7, 74.54999999999998, 113.0, 0.7275628989861059, 0.11581323489720241, 0.0], "isController": false}, {"data": ["Listado paginado de logs", 57, 0, 0.0, 1.0526315789473686, 0, 3, 1.0, 1.2000000000000028, 2.0, 3.0, 0.7250063597049097, 2.564426791846858, 0.0], "isController": false}, {"data": ["Sesion tipica: panel + hallazgos + logs", 55, 0, 0.0, 339.69090909090914, 310, 1098, 321.0, 347.4, 367.19999999999993, 1098.0, 0.6961937190668473, 6.919920811920102, 0.0], "isController": true}, {"data": ["Hallazgos por severidad", 60, 0, 0.0, 0.8333333333333333, 0, 2, 1.0, 1.0, 1.0, 2.0, 0.7346548958626685, 0.035871821087044356, 0.0], "isController": false}, {"data": ["Logs filtrados por origen", 55, 0, 0.0, 1.727272727272727, 1, 3, 2.0, 2.0, 2.1999999999999957, 3.0, 0.7025701292729039, 1.793474919843135, 0.0], "isController": false}, {"data": ["Top talkers (bytes)", 61, 0, 0.0, 50.34426229508197, 44, 60, 50.0, 54.800000000000004, 56.9, 60.0, 0.7237521208310098, 0.19648739217873118, 0.0], "isController": false}, {"data": ["Top puertos destino", 60, 0, 0.0, 36.23333333333333, 33, 51, 35.0, 39.0, 41.949999999999996, 51.0, 0.7397270407219736, 0.11630473980101343, 0.0], "isController": false}]}, function(index, item){
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
    createTable($("#top5ErrorsBySamplerTable"), {"supportsControllersDiscrimination": false, "overall": {"data": ["Total", 529, 0, "", "", "", "", "", "", "", "", "", ""], "isController": false}, "titles": ["Sample", "#Samples", "#Errors", "Error", "#Errors", "Error", "#Errors", "Error", "#Errors", "Error", "#Errors", "Error", "#Errors"], "items": [{"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}]}, function(index, item){
        return item;
    }, [[0, 0]], 0);

});
