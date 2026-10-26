// Authorization token that must have been created previously. See : https://developer.spotify.com/documentation/web-api/concepts/authorization
const token = 'BQDdm-P78jwl2P84rneREgJCT4-lOc-3qkGbvmlPSEv5oFewt6PJPxu0q2lXXcTJWDSnFgioS0j0iySu5bpAV-iTK1zaZtyuXsaKJtvxix1E8-B8ANiU_RTkMGjdASTTuC2vWK9DkL1HEPl2D46LIcJTk66-Jd1N26Xd8WxQIFLFVlifWJ3Xy9ZliIMfvAm9pE6GdgimNzpO7rdNaFx5Egi_8bg5xW1sowPzol6Vm1PKCsmoUIIz4_bNnG9nIF6FUV_7IixTdPO5nNQoLbpCo_DDa3fkVcqV5286lhKf_J6an6NFIFQ5edkQRtVJOnyhI3C_hFar';
async function fetchWebApi(endpoint, method, body) {
  const res = await fetch(`https://api.spotify.com/${endpoint}`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
    method,
    body:JSON.stringify(body)
  });
  return await res.json();
}

async function getTopTracks(){
  // Endpoint reference : https://developer.spotify.com/documentation/web-api/reference/get-users-top-artists-and-tracks
  return (await fetchWebApi(
    'v1/me/top/tracks?time_range=long_term&limit=10', 'GET'
  )).items;
}

const topTracks = await getTopTracks();
console.log(
  topTracks?.map(
    ({name, artists}) =>
      `${name} by ${artists.map(artist => artist.name).join(', ')}`
  )
);