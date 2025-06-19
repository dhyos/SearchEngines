<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;

class SearchController extends Controller {
    
    public function query(Request $request)
{
    // Ambil query dari input (GET)
    $query = $request->query('query', '');

    // Pastikan selalu string
    $query = trim((string) $query);

    // Cache per 60 detik berdasarkan query
    $data = cache()->remember("search_" . md5($query), 60, function () use ($query) {
        if ($query === '') {
            return []; // Jika kosong, kembalikan array kosong
        }

        // Escape query agar aman dieksekusi di shell
        $escapedQuery = escapeshellarg($query);

        // Jalankan script Python dengan parameter
        $output = shell_exec("py query.py indexDB 10 {$escapedQuery}");

        // Pisahkan per baris dan filter
        $lines = array_filter(explode("\n", $output));

        // Gabungkan setiap JSON object multiline
        $results = [];
        $current = '';

        foreach ($lines as $line) {
            $line = trim($line);
            if ($line === '{') {
                $current = '{';
            } elseif ($line === '}') {
                $current .= '}';
                $results[] = json_decode($current, true);
                $current = '';
            } else {
                $current .= $line;
            }
        }

        return $results;
    });

    // Kirim data dan query ke view
    return view("search", [
        "query" => $query,
        "data" => $data
    ]);
}

}
