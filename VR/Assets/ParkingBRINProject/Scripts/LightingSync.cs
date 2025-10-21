using UnityEngine;
using System;

public class LightingSync : MonoBehaviour
{
    [Header("Config")]
    public float latitudeTilt = 0f;
    public Light sunLight;

    void Awake()
    {
        // Biar object ini nggak hancur saat ganti scene
        DontDestroyOnLoad(gameObject);

        // Cek kalau sudah ada matahari lain (biar nggak dobel)
        var lights = FindObjectsOfType<LightingSync>();
        if (lights.Length > 1)
        {
            Destroy(gameObject); // Hapus duplikat
        }
    }

    void Update()
    {
        DateTime now = DateTime.Now;
        float hours = now.Hour + now.Minute / 60f + now.Second / 3600f;

        // Dibalik arahnya dengan dikasih minus
        float rotationY = -(hours / 24f) * 360f;

        // Rotasi matahari (X = naik turun, Y = arah timur-barat, Z = tilt bumi opsional)
        transform.rotation = Quaternion.Euler(
            (hours / 24f) * 360f - 90f,
            rotationY,
            latitudeTilt
        );

        // Kontrol intensitas cahaya
        if (sunLight != null)
        {
            if (hours >= 6 && hours <= 18)
                sunLight.intensity = 1f;
            else
                sunLight.intensity = 0f;
        }
    }
}
