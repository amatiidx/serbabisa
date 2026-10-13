<?php
// Salin jadi config.php lalu isi. JANGAN upload config.php ke GitHub.
return [
    'mode'          => 'production',            // 'sandbox' untuk uji coba
    'merchant_code' => 'D25220',
    'api_key'       => 'ISI_API_KEY_DI_SINI',
    'callback_url'  => 'https://master.serbabisa.id/portal.php',
    'return_url'    => 'https://master.serbabisa.id/portal.php',
    'expiry_menit'  => 1440,                    // batas bayar 24 jam

    // Database billing (MySQL)
    'db_dsn'  => 'mysql:host=localhost;dbname=NAMA_DB;charset=utf8mb4',
    'db_user' => 'USER_DB',
    'db_pass' => 'PASS_DB',
];
