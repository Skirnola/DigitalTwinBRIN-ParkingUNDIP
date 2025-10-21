using UnityEngine;

public class RespawnPlayer : MonoBehaviour
{
    [Header("Respawn Settings")]
    public Transform respawnPoint;   
    public float fallThreshold = -5f;

    private void Update()
    {
        if (transform.position.y < fallThreshold)
        {
            if (respawnPoint != null)
            {
                transform.position = respawnPoint.position;
                transform.rotation = respawnPoint.rotation;
            }
            else
            {
                transform.position = new Vector3(0, 1.5f, 0);
                transform.rotation = Quaternion.identity;
            }
        }
    }
}
