using UnityEngine;
using System;

public class RealtimeLighting : MonoBehaviour
{
    [Header("Config")]
    public float latitudeTilt = 0f;
    public Light sunLight;

    void Update()
    {
        DateTime now = DateTime.Now;
        float hours = now.Hour + now.Minute / 60f + now.Second / 3600f;

        // Dibalik arahnya dengan dikasih minus
        float rotationY = -(hours / 24f) * 360f;

        // Rotasi matahari (X = naik turun, Y = arah timur-barat, Z = tilt bumi opsional) inget bal
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
