<?php

// 1) Подключаемся к базе
$db = new PDO('sqlite:algo.db');
$db->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);

/**
 * Функция получения истории Bybit (вставьте сюда тот код,
 * который у вас уже есть, или сделайте include("bybit_api.php") и т.п.)
 */
function getBybitTradeHistory($apiKey, $secretKey) {
    // ВАШ исходный код, возвращающий массив сделок
    // Ниже — укороченный пример для наглядности
    $url = "https://api.bybit.com/v5/position/closed-pnl";

    $params = [
        'category'   => 'linear',
        'settleCoin' => 'USDT',
        'limit'      => '200'
    ];

    $recvWindow = 5000;
    $timestamp  = round(microtime(true) * 1000);

    ksort($params);
    $queryString = http_build_query($params);

    $stringToSign = $timestamp . $apiKey . $recvWindow . $queryString;
    $signature = hash_hmac('sha256', $stringToSign, $secretKey);

    $headers = [
        "Content-Type: application/json",
        "X-BAPI-API-KEY: $apiKey",
        "X-BAPI-SIGN: $signature",
        "X-BAPI-TIMESTAMP: $timestamp",
        "X-BAPI-RECV-WINDOW: $recvWindow"
    ];

    $finalUrl = $url . "?" . $queryString;

    $ch = curl_init();
    curl_setopt($ch, CURLOPT_URL, $finalUrl);
    curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    $response = curl_exec($ch);
    $curlErr  = curl_error($ch);
    curl_close($ch);

    if ($curlErr) {
        // Логируем или как-то обрабатываем
        return [];
    }

    $data = json_decode($response, true);
    if (!isset($data['result']['list'])) {
        return [];
    }

    $trades = [];
    foreach ($data['result']['list'] as $item) {
        $trades[] = [
            'symbol'         => $item['symbol']         ?? '',
            'side'           => $item['side']           ?? '',
            'closedPnl'      => $item['closedPnl']      ?? '',
            'avgEntryPrice'  => $item['avgEntryPrice']  ?? '',
            'avgExitPrice'   => $item['avgExitPrice']   ?? '',
            'createdTime'    => $item['createdTime']    ?? '',
            'updatedTime'    => $item['updatedTime']    ?? '',
            'leverage'       => $item['leverage']       ?? '',
            'qty'            => $item['qty']            ?? '',
            'execType'       => $item['execType']       ?? '',
            'fillCount'      => $item['fillCount']      ?? ''
        ];
    }
    return $trades;
}

// -------------------------------------------------------------------
// 2) Получаем все конфиги + связанные аккаунты
//    (допустим, вы храните user_id в сессии, но раз это скрипт для CRON,
//     можно либо брать user_id = 1, либо обновлять для всех пользователей).
// -------------------------------------------------------------------
$sql = "
    SELECT c.id AS config_id,
           c.coin,
           c.tf,
           a.id AS acc_id,
           a.api_key,
           a.api_secret,
           a.exchange
      FROM configs c
      JOIN accounts a ON c.account_id = a.id
";
$stmt = $db->query($sql);
$configs = $stmt->fetchAll(PDO::FETCH_ASSOC);

if (!$configs) {
    echo "No configs found.\n";
    exit;
}

// -------------------------------------------------------------------
// 3) Для каждого конфига — подгружаем сделок с Bybit и сохраняем
//    в таблицу trade_history
// -------------------------------------------------------------------
$insertSql = "
INSERT OR IGNORE INTO trade_history
(config_id, symbol, side, qty, closed_pnl, avg_entry_price, avg_exit_price,
 created_time, updated_time, leverage, exec_type, fill_count)
VALUES
(:config_id, :symbol, :side, :qty, :closed_pnl, :avg_entry_price, :avg_exit_price,
 :created_time, :updated_time, :leverage, :exec_type, :fill_count)
";

$insertStmt = $db->prepare($insertSql);

foreach ($configs as $cfg) {
    // 3.1) Если биржа = bybit — вызываем нашу функцию
    if ($cfg['exchange'] === 'bybit') {
        $apiKey = $cfg['api_key'];
        $secretKey = $cfg['api_secret'];

        echo "Loading trades for config_id={$cfg['config_id']} ({$cfg['coin']} {$cfg['tf']})...\n";
        $trades = getBybitTradeHistory($apiKey, $secretKey);

        // 3.2) Добавляем в таблицу
        $countAdded = 0;
        foreach ($trades as $t) {
            $insertStmt->execute([
                ':config_id'       => $cfg['acc_id'],
                ':symbol'          => $t['symbol'],
                ':side'            => $t['side'],
                ':qty'             => $t['qty'],
                ':closed_pnl'      => $t['closedPnl'],
                ':avg_entry_price' => $t['avgEntryPrice'],
                ':avg_exit_price'  => $t['avgExitPrice'],
                ':created_time'    => $t['createdTime'],
                ':updated_time'    => $t['updatedTime'],
                ':leverage'        => $t['leverage'],
                ':exec_type'       => $t['execType'],
                ':fill_count'      => $t['fillCount'],
            ]);
            // INSERT OR IGNORE не бросит ошибку, если такая запись уже есть
            // Проверим кол-во затронутых строк
            if ($insertStmt->rowCount() > 0) {
                $countAdded++;
            }
        }
        echo "New trades inserted: $countAdded\n";
    }
    else {
        echo "Config #{$cfg['config_id']}: exchange not bybit, skipping.\n";
    }
}

echo "Done.\n";
