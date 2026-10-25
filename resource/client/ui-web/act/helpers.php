<?php
// Shared request schemas for the authenticated action endpoints.
function gwd_rows(string $key, array $fields): array
{
    $rows = $_POST[$key] ?? [];
    if (!is_array($rows) || !array_is_list($rows)) gwd_fail(400, 'Invalid ' . $key);
    foreach ($rows as $row) {
        if (!is_array($row) || count($row) !== count($fields) ||
            array_diff(array_keys($row), $fields) !== [] || array_diff($fields, array_keys($row)) !== []) {
            gwd_fail(400, 'Invalid ' . $key);
        }
        foreach ($row as $value) {
            if (!is_string($value)) gwd_fail(400, 'Invalid ' . $key);
        }
    }
    return $rows;
}

function gwd_restore_upload(string $name): string
{
    $file = $_FILES['file'] ?? null;
    if (!is_array($file) || ($file['error'] ?? null) !== UPLOAD_ERR_OK ||
        ($file['name'] ?? null) !== $name || !is_string($file['tmp_name'] ?? null) ||
        !is_uploaded_file($file['tmp_name'])) gwd_fail(400, 'Invalid upload');
    $config = json_decode(file_get_contents($file['tmp_name']), true);
    if (!is_array($config) || !isset($config['address'], $config['v2node']) ||
        !is_array($config['address']) || !is_array($config['v2node'])) gwd_fail(400, 'Invalid backup');
    $source = $file['tmp_name'];
    $id = bin2hex(random_bytes(16));
    $target = '/var/lib/de_GWD/uploads/' . $id;
    if (!move_uploaded_file($source, $target)) gwd_fail(500, 'Upload failed');
    chmod($target, 0600);
    return $id;
}
