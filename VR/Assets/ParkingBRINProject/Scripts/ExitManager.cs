using UnityEngine;
using UnityEngine.SceneManagement;
using Firebase.Auth;
using UnityEngine.XR.Management;

public class ExitManager : MonoBehaviour
{
    private FirebaseAuth auth;

    void Start()
    {
        auth = FirebaseAuth.DefaultInstance;
    }

    public void Exit()
    {
        auth.SignOut();
        Debug.Log("User logged out.");
        StartCoroutine(RestartAfterExit());
    }

    private System.Collections.IEnumerator RestartAfterExit()
    {
        XRGeneralSettings.Instance.Manager.StopSubsystems();
        XRGeneralSettings.Instance.Manager.DeinitializeLoader();

        SceneManager.LoadScene("LoginSignup");

        yield return null;

        XRGeneralSettings.Instance.Manager.InitializeLoaderSync();
        XRGeneralSettings.Instance.Manager.StartSubsystems();
    }
}
